"""Test writer: generates tests/test_feature.py, repair loops, and tests/test.sh."""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from taskforge.proposer import ProposedTask
from taskforge.llm import LLMClient

class TestWriter:
    def __init__(self, config_dict: Optional[Dict[str, Any]] = None, offline: bool = False):
        self.config_dict = config_dict
        self.offline = offline
        self.llm = LLMClient(config=config_dict)

    def generate_feature_test(self, task: ProposedTask) -> str:
        """Generates feature test suite via LLM when online, or from task definition."""
        if not self.offline and self.llm.is_available() and not task.test_feature_code:
            prompt = f"""You are a senior QA engineer. Write a complete pytest suite for this feature:
TASK: {task.feature_name}
SUMMARY: {task.summary}
SIGNATURE: {task.signature}
TARGET MODULES: {task.target_modules}

CRITICAL RULES:
- Test nominal functionality, edge cases (zero, negative, empty, None), and error handling.
- Assert exact return values, state transitions, and expected exceptions with pytest.raises.
- Return strictly parseable Python code."""
            try:
                code, _ = self.llm.call("generator", prompt, max_tokens=2048)
                cleaned = code.strip()
                if "```python" in cleaned:
                    cleaned = cleaned.split("```python")[1].split("```")[0].strip()
                elif "```" in cleaned:
                    cleaned = cleaned.split("```")[1].split("```")[0].strip()
                if len(cleaned) > 50:
                    return cleaned + "\n"
            except Exception:
                pass

        return task.test_feature_code.strip() + "\n"

    def repair_tests_for_mutants(
        self,
        instruction_md: str,
        current_tests: str,
        surviving_mutants: List[Dict[str, Any]],
        round_idx: int = 1
    ) -> Optional[str]:
        """Feeds surviving mutants back to the test-writer LLM to enhance test kill rate."""
        if not self.llm.is_available():
            return None

        diffs_summary = "\n\n".join([
            f"--- Mutant {m['mutant_id']} ({m['operator']}) ---\n{m['diff']}"
            for m in surviving_mutants[:6]
        ])

        prompt = f"""You are a senior QA engineer improving a pytest test suite to catch surviving code mutations.

SPECIFICATION:
{instruction_md}

SURVIVING CODE MUTATIONS THAT PASSED THE TESTS:
{diffs_summary}

CURRENT TEST SUITE:
{current_tests}

TASK:
Write updated or additional pytest test functions to catch and kill these surviving mutations.
- Check boundaries, off-by-one errors, comparison flips, default returns, and dropped validations.
- Strictly adhere to the requirements in instruction.md without asserting unspecified behavior.
- Return strictly the complete, updated Python code for tests/test_feature.py."""

        try:
            raw_code, model_used = self.llm.call("generator", prompt, max_tokens=2048)
            cleaned = raw_code.strip()
            if "```python" in cleaned:
                cleaned = cleaned.split("```python")[1].split("```")[0].strip()
            elif "```" in cleaned:
                cleaned = cleaned.split("```")[1].split("```")[0].strip()
            if "def test_" in cleaned:
                return cleaned + "\n"
        except Exception as e:
            print(f"[!] Test repair round {round_idx} failed: {e}")
            return None

        return None

    def generate_test_sh(self, task: ProposedTask) -> str:
        return '''#!/bin/bash
set -u

mkdir -p /logs/verifier
REWARD_FILE="/logs/verifier/reward.txt"

echo "=== Running TaskForge Verifier Suite for: ''' + task.task_id + ''' ==="

echo "--- Running Feature Tests ---"
if pytest -v tests/test_feature.py; then
    FEATURE_PASS=1
    echo "Feature tests: PASSED"
else
    FEATURE_PASS=0
    echo "Feature tests: FAILED"
fi

echo "--- Running Regression Tests ---"
REG_TESTS=$(find tests -maxdepth 1 -name "test_*.py" ! -name "test_feature.py")
if [ -z "$REG_TESTS" ] || pytest -v $REG_TESTS; then
    REGRESSION_PASS=1
    echo "Regression tests: PASSED"
else
    REGRESSION_PASS=0
    echo "Regression tests: FAILED"
fi

if [ "$FEATURE_PASS" -eq 1 ] && [ "$REGRESSION_PASS" -eq 1 ]; then
    echo "1" > "$REWARD_FILE"
    echo "=== VERIFIER OUTCOME: SUCCESS (Reward: 1) ==="
    exit 0
else
    echo "0" > "$REWARD_FILE"
    echo "=== VERIFIER OUTCOME: FAILURE (Reward: 0) ==="
    exit 1
fi
'''
