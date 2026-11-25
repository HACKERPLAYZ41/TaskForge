"""LLM Integration Layer via LiteLLM supporting OpenRouter, Anthropic, and local endpoints.
Provides prompt caching, rate-limit backoff, daily call budget enforcement, and audit logging.
"""
import hashlib
import json
import os
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Tuple
import litellm

class LLMProviderError(Exception):
    pass

class LLMBudgetExhaustedError(LLMProviderError):
    """Raised when the LLM provider daily call limit/budget is exhausted."""
    pass

class LLMClient:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        provider_cfg = self.config.get("provider", {})
        self.provider_name = provider_cfg.get("name", "openrouter")
        self.api_key_env = provider_cfg.get("api_key_env", "OPENROUTER_API_KEY")
        self.call_delay_sec = float(provider_cfg.get("call_delay_sec", 1.5))
        
        cache_dir_rel = provider_cfg.get("cache_dir", ".cache/llm")
        self.cache_dir = Path.home() / "taskforge" / cache_dir_rel
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.budget_file = self.cache_dir / "budget_status.json"
        self.log_file = Path.home() / "taskforge" / "logs" / "llm_calls.jsonl"
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.roles = self.config.get("roles", {
            "generator": {
                "primary": "openrouter/baidu/ernie-5.5-flash-preview:free",
                "fallbacks": [
                    "openrouter/nvidia/nemotron-3.5-lightning:free",
                    "openrouter/google/gemma-4-31b-it:free"
                ]
            },
            "judge": {
                "primary": "openrouter/nvidia/nemotron-3.5-lightning:free",
                "fallbacks": [
                    "openrouter/nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
                    "openrouter/baidu/ernie-5.5-flash-preview:free"
                ]
            },
            "agent": {
                "primary": "openrouter/baidu/ernie-5.5-flash-preview:free",
                "eval_model_2": "openrouter/nvidia/nemotron-3.5-lightning:free",
                "fallbacks": [
                    "openrouter/google/gemma-4-31b-it:free"
                ]
            }
        })
        self._last_call_time = 0.0

    def get_budget_status(self) -> Dict[str, Any]:
        """Returns budget exhaustion status from disk or default."""
        if self.budget_file.exists():
            try:
                return json.loads(self.budget_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {"exhausted": False, "reason": None, "timestamp": None}

    def mark_budget_exhausted(self, reason: str):
        """Marks the daily call budget as permanently exhausted for the session."""
        status = {
            "exhausted": True,
            "reason": reason,
            "timestamp": time.time(),
            "date": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
        }
        try:
            self.budget_file.write_text(json.dumps(status, indent=2), encoding="utf-8")
        except Exception:
            pass

    def is_budget_exhausted(self) -> bool:
        return bool(self.get_budget_status().get("exhausted", False))

    def get_model_for_role(self, role: str) -> str:
        role_cfg = self.roles.get(role, {})
        return role_cfg.get("primary", "openrouter/baidu/ernie-5.5-flash-preview:free")

    def get_api_key(self) -> Optional[str]:
        val = os.getenv(self.api_key_env)
        if val and len(val.strip()) > 0:
            return val.strip()
        if self.provider_name == "openrouter":
            v = os.getenv("OPENROUTER_API_KEY")
            if v and len(v.strip()) > 0:
                return v.strip()
        elif self.provider_name == "anthropic":
            v = os.getenv("ANTHROPIC_API_KEY")
            if v and len(v.strip()) > 0:
                return v.strip()
        return None

    def is_available(self) -> bool:
        if self.is_budget_exhausted():
            return False
        return self.get_api_key() is not None

    def _get_cache_path(self, model: str, prompt: str, system_prompt: Optional[str]) -> Path:
        key_data = f"{model}::{system_prompt or ''}::{prompt}"
        h = hashlib.sha256(key_data.encode("utf-8")).hexdigest()
        return self.cache_dir / f"{h}.json"

    def _log_call(self, role: str, model: str, cached: bool, latency: float, status: str, error: Optional[str] = None):
        record = {
            "timestamp": time.time(),
            "role": role,
            "model": model,
            "cached": cached,
            "latency": round(latency, 3),
            "status": status,
            "error": error
        }
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    def call(
        self,
        role: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        use_cache: bool = True,
        max_retries: int = 2,
        max_tokens: int = 2048,
        temperature: float = 0.2
    ) -> Tuple[str, str]:
        """Calls LLM for a given role. Fails fast without retry if budget exhausted."""
        # Fail immediately if daily quota is already exhausted
        if self.is_budget_exhausted():
            b_info = self.get_budget_status()
            raise LLMBudgetExhaustedError(
                f"STOP: OpenRouter free-models-per-day daily limit is exhausted. Reason: {b_info.get('reason')}"
            )

        api_key = self.get_api_key()
        if not api_key:
            raise LLMProviderError(f"No API key configured for environment variable '{self.api_key_env}'.")

        role_cfg = self.roles.get(role, {})
        primary_model = role_cfg.get("primary", "openrouter/baidu/ernie-5.5-flash-preview:free")
        fallbacks = role_cfg.get("fallbacks", [])
        models_to_try = [primary_model] + [m for m in fallbacks if m != primary_model]

        # Enforce rate limit delay
        elapsed = time.time() - self._last_call_time
        if elapsed < self.call_delay_sec:
            time.sleep(self.call_delay_sec - elapsed)

        last_error = None
        for model in models_to_try:
            cache_path = self._get_cache_path(model, prompt, system_prompt)
            if use_cache and cache_path.exists():
                try:
                    data = json.loads(cache_path.read_text(encoding="utf-8"))
                    self._log_call(role, model, cached=True, latency=0.0, status="SUCCESS")
                    return data["content"], model
                except Exception:
                    pass

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            for attempt in range(max_retries):
                t0 = time.time()
                try:
                    self._last_call_time = time.time()
                    resp = litellm.completion(
                        model=model,
                        messages=messages,
                        api_key=api_key,
                        max_tokens=max_tokens,
                        temperature=temperature
                    )
                    latency = time.time() - t0
                    msg = resp.choices[0].message
                    content = msg.content or getattr(msg, "reasoning_content", None) or ""
                    content = content.strip()
                    if not content and hasattr(msg, "text"):
                        content = (msg.text or "").strip()

                    if not content:
                        raise ValueError(f"Empty completion content returned from model {model}.")

                    if use_cache:
                        cache_path.write_text(json.dumps({"content": content, "model": model}), encoding="utf-8")

                    self._log_call(role, model, cached=False, latency=latency, status="SUCCESS")
                    return content, model

                except Exception as e:
                    latency = time.time() - t0
                    err_msg = str(e)
                    self._log_call(role, model, cached=False, latency=latency, status="ERROR", error=err_msg)
                    last_error = e

                    # Check for daily free model exhaustion
                    if "free-models-per-day" in err_msg or "daily limit" in err_msg.lower() or "free_tier_daily" in err_msg:
                        self.mark_budget_exhausted(f"OpenRouter free-tier daily quota exhausted: {err_msg[:200]}")
                        raise LLMBudgetExhaustedError(
                            "STOP: OpenRouter free-models-per-day limit is exhausted. Do not retry in a loop."
                        ) from e

                    if "429" in err_msg or "rate limit" in err_msg.lower() or "503" in err_msg:
                        time.sleep(2.0)
                        continue
                    else:
                        break

        raise LLMProviderError(f"Exhausted model attempts for role '{role}'. Last error: {last_error}")

    def call_structured(
        self,
        role: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_retries: int = 2
    ) -> Tuple[Dict[str, Any], str]:
        """Calls LLM and parses JSON output. Stops immediately on budget exhaustion."""
        json_instruction = "\nYou must output ONLY valid, strictly parseable JSON conforming to the requested schema. No surrounding explanation, no markdown outside the JSON block."
        effective_prompt = prompt + json_instruction

        last_raw = ""
        last_model = ""
        for attempt in range(max_retries):
            raw_text, model = self.call(role, effective_prompt, system_prompt=system_prompt, use_cache=True)
            last_raw = raw_text
            last_model = model

            cleaned = raw_text.strip()
            if "```json" in cleaned:
                cleaned = cleaned.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned:
                cleaned = cleaned.split("```")[1].split("```")[0].strip()

            s_idx = cleaned.find("{")
            e_idx = cleaned.rfind("}")
            if s_idx != -1 and e_idx != -1 and e_idx > s_idx:
                candidate = cleaned[s_idx:e_idx + 1]
                try:
                    parsed = json.loads(candidate)
                    if isinstance(parsed, dict):
                        return parsed, model
                except json.JSONDecodeError:
                    pass

            effective_prompt = f"The previous response was not valid JSON:\n{last_raw[:400]}\n\nPlease re-format your response into valid JSON conforming exactly to the requested schema:"

        raise LLMProviderError(f"Failed to obtain valid JSON from role '{role}' ({last_model}) after {max_retries} attempts.")
