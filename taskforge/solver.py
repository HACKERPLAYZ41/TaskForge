"""Reference solver: generates reference code modifications and solve.sh patch."""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from taskforge.proposer import ProposedTask
from taskforge.llm import LLMClient

class ReferenceSolver:
    def __init__(self, config_dict: Optional[Dict[str, Any]] = None, offline: bool = False):
        self.config_dict = config_dict
        self.offline = offline
        self.llm = LLMClient(config=config_dict)

    def generate_solve_script(self, task: ProposedTask, base_repo_dir: Path) -> str:
        """Generates solution/solve.sh that modifies target files cleanly via search/replace."""
        solution_map = dict(task.solution_code_map)

        lines = [
            "#!/bin/bash",
            "set -e",
            "",
            f"# TaskForge Reference Solution for: {task.task_id}",
            'if [ -d "/workspace/repo" ]; then',
            '    cd /workspace/repo',
            'fi',
            ""
        ]

        # Handle structured search-and-replace edits using safe heredoc
        for mod_rel, edit_data in solution_map.items():
            if isinstance(edit_data, dict) and "target" in edit_data and "replacement" in edit_data:
                target_json = json.dumps(edit_data["target"])
                replacement_json = json.dumps(edit_data["replacement"])
                py_script = f'''python3 - << 'PYEOF'
import json
from pathlib import Path

p = Path('{mod_rel}')
content = p.read_text(encoding='utf-8')
target = json.loads({json.dumps(target_json)})
replacement = json.loads({json.dumps(replacement_json)})
assert target in content, f'Search target not found in {{p}}'
content = content.replace(target, replacement, 1)
p.write_text(content, encoding='utf-8')
PYEOF'''
                lines.append(py_script)
                lines.append("")
            elif isinstance(edit_data, list):
                # Multiple search/replace edits in sequence
                edits_json = json.dumps(edit_data)
                py_script = f'''python3 - << 'PYEOF'
import json
from pathlib import Path

p = Path('{mod_rel}')
content = p.read_text(encoding='utf-8')
edits = json.loads({json.dumps(edits_json)})
for item in edits:
    target = item['target']
    replacement = item['replacement']
    assert target in content, f'Search target not found in {{p}}'
    content = content.replace(target, replacement, 1)
p.write_text(content, encoding='utf-8')
PYEOF'''
                lines.append(py_script)
                lines.append("")
            elif isinstance(edit_data, str):
                clean_code = edit_data.strip("\n")
                if clean_code.startswith("# SCRIPT:"):
                    lines.append(clean_code.replace("# SCRIPT:", "", 1).strip())
                elif clean_code.startswith("# FULL_REPLACE"):
                    body = clean_code.replace("# FULL_REPLACE", "", 1).strip("\n")
                    lines.append(f"cat << 'EOF' > {mod_rel}")
                    lines.append(body)
                    lines.append("EOF")
                else:
                    lines.append(f"cat << 'EOF' >> {mod_rel}")
                    lines.append(clean_code)
                    lines.append("EOF")
                lines.append("")

        return "\n".join(lines) + "\n"
