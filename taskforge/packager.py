"""Harbor Task Packager: builds valid Harbor 0.25 task structure."""
import ast
import json
from pathlib import Path
import shutil
from typing import Any, Dict, List, Optional
import toml
from taskforge.proposer import ProposedTask
from taskforge.spec_writer import SpecWriter
from taskforge.solver import ReferenceSolver
from taskforge.test_writer import TestWriter

class HarborPackager:
    def __init__(self, target_repo_path: Path, config_dict: Optional[Dict[str, Any]] = None, offline: bool = False):
        self.target_repo_path = Path(target_repo_path).resolve()
        self.config_dict = config_dict or {}
        self.offline = offline
        self.spec_writer = SpecWriter(config_dict=config_dict, offline=offline)
        self.solver = ReferenceSolver(config_dict=config_dict, offline=offline)
        self.test_writer = TestWriter(config_dict=config_dict, offline=offline)

    def extract_test_nodes(self, test_feature_code: str) -> List[str]:
        """Extracts pytest node IDs from feature test code."""
        nodes = []
        try:
            tree = ast.parse(test_feature_code)
            for n in ast.walk(tree):
                if isinstance(n, ast.FunctionDef) and n.name.startswith("test_"):
                    nodes.append(f"tests/test_feature.py::{n.name}")
        except Exception:
            pass
        return nodes or ["tests/test_feature.py"]

    def package(self, task: ProposedTask, output_dir: Path, commit_hash: str) -> Path:
        task_dir = output_dir / task.task_id
        if task_dir.exists():
            shutil.rmtree(task_dir)
        task_dir.mkdir(parents=True, exist_ok=True)

        env_dir = task_dir / "environment"
        env_dir.mkdir()
        sol_dir = task_dir / "solution"
        sol_dir.mkdir()
        tests_dir = task_dir / "tests"
        tests_dir.mkdir()

        base_commit = self.config_dict.get("base_commit", commit_hash or "934813e4d421071a1b3db3973c02fe2721359a6e")
        repo_url = self.config_dict.get("repo_url", "https://github.com/pallets/click.git")
        repo_id = self.config_dict.get("repo_identifier", "pallets/click")
        license_name = self.config_dict.get("license", "BSD-3-Clause")
        harbor_ver = self.config_dict.get("harbor_version", "0.25.0")

        # 1. task.toml (Harbor v0.25 compliant)
        task_toml_data = {
            "schema_version": "1.4",
            "task": {
                "name": f"taskforge/{task.task_id}",
                "authors": [{"name": "TaskForge Pipeline", "email": "taskforge@innodata.ai"}]
            },
            "metadata": {
                "repo_identifier": repo_id,
                "repo_url": repo_url,
                "base_commit": base_commit,
                "license": license_name,
                "harbor_version": harbor_ver,
                "feature_type": task.feature_type,
                "difficulty": task.difficulty,
                "seed": task.seed,
                "generator_version": "1.0.0",
                "provider": getattr(task, "provider", "openrouter"),
                "model": getattr(task, "model", "default"),
                "summary": task.summary
            },
            "verifier": {
                "timeout_sec": 120.0,
                "user": "root",
                "environment_mode": "shared",
                "network_mode": "no-network"
            },
            "agent": {
                "timeout_sec": 300.0,
                "user": "root"
            },
            "environment": {
                "cpus": 1,
                "memory_mb": 2048,
                "storage_mb": 4096
            }
        }
        (task_dir / "task.toml").write_text(toml.dumps(task_toml_data), encoding="utf-8")

        # 2. instruction.md
        instruction_md = self.spec_writer.generate_instruction(task)
        (task_dir / "instruction.md").write_text(instruction_md, encoding="utf-8")

        # 3. environment/Dockerfile (clean clone at base_commit, NO local copy committed)
        dockerfile_content = f'''FROM python:3.12-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends \\
    git \\
    locales \\
    && rm -rf /var/lib/apt/lists/*
RUN echo "en_US.UTF-8 UTF-8" > /etc/locale.gen && locale-gen
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8
WORKDIR /workspace/repo
RUN git clone {repo_url} . && \\
    git checkout {base_commit}
RUN pip install --no-cache-dir -e . pytest==8.3.4
'''
        (env_dir / "Dockerfile").write_text(dockerfile_content, encoding="utf-8")

        # 4. solution/solve.sh (surgical search/replace)
        solve_sh = self.solver.generate_solve_script(task, self.target_repo_path)
        solve_path = sol_dir / "solve.sh"
        solve_path.write_text(solve_sh, encoding="utf-8")
        solve_path.chmod(0o755)

        # 5. tests/test_feature.py
        test_feature_py = self.test_writer.generate_feature_test(task)
        (tests_dir / "test_feature.py").write_text(test_feature_py, encoding="utf-8")

        # 6. tests/fail_to_pass.json
        fail_nodes = self.extract_test_nodes(test_feature_py)
        (tests_dir / "fail_to_pass.json").write_text(json.dumps(fail_nodes, indent=2), encoding="utf-8")

        # 7. tests/pass_to_pass.json
        reg_tests = getattr(task, "regression_tests", ["tests/test_basic.py", "tests/test_commands.py"])
        (tests_dir / "pass_to_pass.json").write_text(json.dumps(reg_tests, indent=2), encoding="utf-8")

        # 8. tests/test.sh (executes both fail_to_pass and pass_to_pass, outputs reward 1 or 0)
        reg_str = " ".join(reg_tests)
        test_sh = f'''#!/bin/bash
mkdir -p /logs/verifier
REWARD_FILE="/logs/verifier/reward.txt"

# Default to 0 so reward file is always present even if test crashes
echo 0 > "$REWARD_FILE"

TEST_FEATURE="/tests/test_feature.py"
if [ ! -f "$TEST_FEATURE" ]; then
    TEST_FEATURE="tests/test_feature.py"
fi

cd /workspace/repo
export PYTHONPATH="src:${{PYTHONPATH:-}}"

# Run feature tests and regression tests
if pytest -q "$TEST_FEATURE" {reg_str}; then
    echo 1 > "$REWARD_FILE"
    echo "=== TaskForge Verifier: SUCCESS (Reward: 1) ==="
    exit 0
else
    echo 0 > "$REWARD_FILE"
    echo "=== TaskForge Verifier: FAILURE (Reward: 0) ==="
    exit 0
fi
'''
        test_sh_path = tests_dir / "test.sh"
        test_sh_path.write_text(test_sh, encoding="utf-8")
        test_sh_path.chmod(0o755)

        return task_dir
