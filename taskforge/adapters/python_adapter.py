"""Python-specific repository adapter."""
import hashlib
import os
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple
from taskforge.adapters.base import RepoAdapter

class PythonAdapter(RepoAdapter):
    def get_commit_hash(self) -> str:
        commit_file = self.repo_path / "COMMIT_HASH"
        if commit_file.exists():
            return commit_file.read_text().strip()
        git_main = self.repo_path / ".git" / "refs" / "heads" / "main"
        if git_main.exists():
            return git_main.read_text().strip()
        hasher = hashlib.sha1()
        for f in sorted(self.repo_path.rglob("*.py")):
            hasher.update(f.read_bytes())
        return hasher.hexdigest()

    def list_modules(self) -> List[Path]:
        mods = []
        for p in sorted(self.repo_path.rglob("*.py")):
            parts = p.parts
            if any(x in parts for x in (".venv", "venv", "tests", ".pytest_cache", "__pycache__")):
                continue
            mods.append(p)
        return mods

    def list_tests(self) -> List[Path]:
        tests = []
        tests_dir = self.repo_path / "tests"
        if tests_dir.exists():
            for p in sorted(tests_dir.rglob("*.py")):
                if p.name.startswith("test_"):
                    tests.append(p)
        return tests

    def run_tests(self, test_cmd: Optional[str] = None, cwd: Optional[Path] = None) -> Tuple[bool, str]:
        work_dir = cwd or self.repo_path
        cmd = test_cmd or "pytest -v"
        
        venv_pytest = Path.home() / "taskforge" / ".venv" / "bin" / "pytest"
        env = os.environ.copy()
        if venv_pytest.exists():
            cmd = f"{venv_pytest} -v"

        proc = subprocess.run(
            cmd,
            shell=True,
            cwd=str(work_dir),
            capture_output=True,
            text=True,
            env=env
        )
        output = proc.stdout + "\n" + proc.stderr
        success = (proc.returncode == 0)
        return success, output

    def apply_patch(self, patch_diff: str, target_dir: Optional[Path] = None) -> bool:
        dest = target_dir or self.repo_path
        proc = subprocess.run(
            ["patch", "-p1", "--batch", "--forward"],
            cwd=str(dest),
            input=patch_diff,
            text=True,
            capture_output=True
        )
        return proc.returncode == 0
