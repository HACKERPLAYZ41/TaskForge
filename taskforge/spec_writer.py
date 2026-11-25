"""Generates behavior-focused instruction.md with concrete test cases and zero solution leakage."""
import ast
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple
from taskforge.proposer import ProposedTask
from taskforge.llm import LLMClient

def check_spec_quality(instruction_text: str) -> Dict[str, Any]:
    """Flags any instruction.md that contains generic phrases without concrete test cases."""
    flags = []
    lower_text = instruction_text.lower()
    
    if "handle boundary conditions" in lower_text:
        flags.append("Contains generic phrase 'handle boundary conditions' without concrete boundary inputs.")
    if "as specified" in lower_text and "input:" not in lower_text and "example:" not in lower_text:
        flags.append("Contains vague phrase 'as specified' without concrete input/output examples.")
        
    has_concrete_cases = any(k in lower_text for k in ["input:", "expected output:", "case 1", "test case", "raises"])
    if not has_concrete_cases:
        flags.append("Missing explicit concrete input/output or exception cases.")
        
    return {
        "passed_quality_check": len(flags) == 0,
        "flags": flags
    }

class SpecWriter:
    def __init__(self, config_dict: Optional[Dict[str, Any]] = None, offline: bool = False):
        self.config_dict = config_dict
        self.offline = offline
        self.llm = LLMClient(config=config_dict)

    def extract_concrete_cases_from_tests(self, test_code: str) -> List[Dict[str, str]]:
        """Extracts concrete input/output requirements from the reference pytest suite."""
        cases = []
        if not test_code:
            return cases

        try:
            tree = ast.parse(test_code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                    title = node.name.replace("test_", "").replace("_", " ").capitalize()
                    doc = ast.get_docstring(node) or ""
                    
                    # Detect raised exceptions
                    raises = []
                    for child in ast.walk(node):
                        if isinstance(child, ast.With):
                            for item in child.items:
                                if isinstance(item.context_expr, ast.Call):
                                    func = item.context_expr.func
                                    if getattr(func, "attr", "") == "raises" or getattr(func, "id", "") == "raises":
                                        if item.context_expr.args:
                                            arg0 = item.context_expr.args[0]
                                            raises.append(getattr(arg0, "id", "Exception"))

                    expected = f"Raises {', '.join(raises)}" if raises else "Succeeds and updates state/returns expected value."
                    cases.append({
                        "case_name": title,
                        "description": doc.strip() if doc else f"Behavior verified by {node.name}.",
                        "expected": expected
                    })
        except Exception:
            pass

        return cases

    def generate_instruction(self, task: ProposedTask) -> str:
        if not self.offline and self.llm.is_available():
            prompt = f"""You are an expert technical specification writer creating a coding benchmark instruction.md.

TASK DETAILS:
- Feature Name: {task.feature_name}
- Taxonomy Category: {task.feature_type}
- Difficulty Tier: {task.difficulty}
- Target Module(s): {', '.join(task.target_modules)}
- Summary: {task.summary}
- Required Signature / Interface: {task.signature}

Write a comprehensive, unambiguous Markdown specification (`instruction.md`) covering:
1. Overview: Problem context and feature purpose.
2. Target Location & Imports: Which file to modify and required classes/functions.
3. Signature & Interface Requirements: Exact arguments, types, defaults, and return type.
4. Behavioral Specifications & Edge Cases: You MUST list concrete cases with specific inputs and expected outputs/exceptions.
   CRITICAL: NEVER write generic phrases like 'handle boundary conditions' or 'as specified'. Detail exact cases.
5. Verification Instructions: Instruct the engineer to verify using `pytest -v tests/test_feature.py`.

CRITICAL RULES:
- Do NOT leak the reference implementation solution code.
- Detail expected observable behavior and concrete input/output mappings only."""
            try:
                content, model_used = self.llm.call("generator", prompt, max_tokens=2048)
                cleaned = content.strip()
                if len(cleaned) > 100:
                    return cleaned + "\n"
            except Exception as e:
                pass

        return self._generate_template(task)

    def _generate_template(self, task: ProposedTask) -> str:
        concrete_cases = self.extract_concrete_cases_from_tests(task.test_feature_code)
        
        case_lines = []
        if concrete_cases:
            for i, c in enumerate(concrete_cases, 1):
                case_lines.append(f"- **Case {i}: {c['case_name']}**")
                case_lines.append(f"  - *Scenario*: {c['description']}")
                case_lines.append(f"  - *Expected Outcome*: {c['expected']}")
        else:
            case_lines.append(f"- **Nominal Execution**: Input valid arguments conforming to `{task.signature}` -> Returns validated result.")
            case_lines.append("- **Invalid/Edge Inputs**: Empty collections, zero or negative quantities -> Raises appropriate domain error or returns documented default.")

        lines = [
            f"# Feature Specification: {task.feature_name}",
            "",
            "## 1. Overview",
            f"{task.summary}",
            "",
            "## 2. Target Location",
            f"- **Target Module(s)**: `{', '.join(task.target_modules)}`",
            f"- **Category / Taxonomy**: `{task.feature_type}`",
            f"- **Difficulty Tier**: `{task.difficulty.upper()}`",
            "",
            "## 3. Interface & Signature Requirements",
            "```python",
            f"{task.signature}",
            "```",
            "",
            "## 4. Behavioral Specifications & Edge Cases",
            "The implementation must satisfy the following concrete behavioral requirements:",
            "",
            "\n".join(case_lines),
            "",
            "- **Backward Compatibility**: All existing repository functionality and baseline tests must continue to pass without regression.",
            "",
            "## 5. Verification",
            "A test suite is provided to verify your implementation. When complete, run:",
            "```bash",
            "pytest -v tests/test_feature.py",
            "```",
            "Ensure both the new feature tests and all regression tests pass."
        ]
        return "\n".join(lines) + "\n"
