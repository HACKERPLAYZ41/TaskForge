"""Autonomous tool-using agent loop for G7 (Solvability Sanity) and Evaluation."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
from typing import Any, Dict, List, Optional, Tuple
from taskforge.llm import LLMClient

class TaskContainerAgent:
    def __init__(self, llm_client: LLMClient, max_turns: int = 20):
        self.llm = llm_client
        self.max_turns = max_turns

    def run_agent_loop(
        self,
        task_dir: Path,
        repo_dir: Path,
        log_file: Path,
        model_role: str = "agent"
    ) -> Dict[str, Any]:
        """Runs autonomous agent loop with access only to instruction.md and repo files."""
        instruction_file = task_dir / "instruction.md"
        instruction_text = instruction_file.read_text(encoding="utf-8") if instruction_file.exists() else ""

        transcript: List[Dict[str, Any]] = []
        start_time = time.time()

        system_prompt = """You are an autonomous AI software engineer working inside a repository.
Your goal is to implement the feature specified in instruction.md.
You have the following tools available:
1. read_file(path: str) -> str: reads file content
2. write_file(path: str, content: str) -> str: writes/overwrites file content
3. run_command(cmd: str) -> str: executes shell command (e.g. pytest -v)
4. finish(message: str) -> str: signals completion

Each turn, respond strictly with a valid JSON object:
{
  "thought": "your step-by-step reasoning",
  "action": "read_file" | "write_file" | "run_command" | "finish",
  "args": { ... }
}
Do NOT include markdown formatting outside the JSON."""

        history_context = [
            f"TASK INSTRUCTION:\n{instruction_text}\n\nAvailable files in repo:\n" + "\n".join(
                [str(p.relative_to(repo_dir)) for p in sorted(repo_dir.rglob("*.py")) if "tests" not in p.parts]
            )
        ]

        turns_executed = 0
        solved = False

        for turn in range(1, self.max_turns + 1):
            turns_executed = turn
            user_prompt = "\n\n".join(history_context[-5:]) + f"\n\nTurn {turn}/{self.max_turns}. Decide your next action."
            
            try:
                step_json, model_used = self.llm.call_structured(model_role, user_prompt, system_prompt=system_prompt)
            except Exception as e:
                transcript.append({
                    "turn": turn,
                    "error": f"LLM call failed: {e}",
                    "timestamp": time.time()
                })
                break

            action = step_json.get("action", "")
            thought = step_json.get("thought", "")
            args = step_json.get("args", {})

            turn_record = {
                "turn": turn,
                "model": model_used,
                "thought": thought,
                "action": action,
                "args": args,
                "timestamp": time.time()
            }

            if action == "finish":
                turn_record["output"] = "Agent declared completion."
                transcript.append(turn_record)
                break

            elif action == "read_file":
                f_path = args.get("path", "")
                target = repo_dir / f_path
                if target.exists() and target.is_file():
                    try:
                        content = target.read_text(encoding="utf-8")
                        tool_out = content[:2000]
                    except Exception as fe:
                        tool_out = f"Error reading file: {fe}"
                else:
                    tool_out = f"File not found: {f_path}"

            elif action == "write_file":
                f_path = args.get("path", "")
                content = args.get("content", "")
                target = repo_dir / f_path
                try:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(content, encoding="utf-8")
                    tool_out = f"Successfully wrote {len(content)} bytes to {f_path}"
                except Exception as we:
                    tool_out = f"Error writing file: {we}"

            elif action == "run_command":
                cmd = args.get("cmd", "")
                if any(cmd.strip().startswith(c) for c in ["pytest", "python", "ls", "cat"]):
                    try:
                        res = subprocess.run(cmd, shell=True, cwd=str(repo_dir), capture_output=True, text=True, timeout=15)
                        tool_out = (res.stdout + "\n" + res.stderr)[:2000]
                    except subprocess.TimeoutExpired:
                        tool_out = "Command timed out after 15s."
                    except Exception as ce:
                        tool_out = f"Command failed: {ce}"
                else:
                    tool_out = f"Command disallowed: {cmd}"

            else:
                tool_out = f"Unknown action: {action}"

            turn_record["output"] = tool_out[:500]
            transcript.append(turn_record)
            history_context.append(f"Action: {action}\nResult:\n{tool_out[:1000]}")

        # Check if agent solved the task by running tests/test_feature.py
        test_feature = task_dir / "tests" / "test_feature.py"
        test_out = ""
        if test_feature.exists():
            dest_test = repo_dir / "tests" / "test_feature.py"
            dest_test.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(test_feature, dest_test)
            res = subprocess.run(["pytest", "-v", "tests/test_feature.py"], cwd=str(repo_dir), capture_output=True, text=True)
            solved = (res.returncode == 0)
            test_out = res.stdout + "\n" + res.stderr

        elapsed = time.time() - start_time
        result = {
            "task_id": task_dir.name,
            "turns_used": turns_executed,
            "max_turns": self.max_turns,
            "agent_solved": solved,
            "elapsed_sec": round(elapsed, 2),
            "test_output": test_out[:1000],
            "transcript": transcript
        }

        log_file.parent.mkdir(parents=True, exist_ok=True)
        log_file.write_text(json.dumps(result, indent=2), encoding="utf-8")
        return result
