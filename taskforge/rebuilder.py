"""Seeded generation reproducibility verifier."""
import hashlib
from pathlib import Path
from typing import Any, Dict, Tuple
from taskforge.proposer import FeatureProposer
from taskforge.packager import HarborPackager

class TaskRebuilder:
    def __init__(self, target_repo_path: Path):
        self.target_repo_path = Path(target_repo_path).resolve()
        self.packager = HarborPackager(self.target_repo_path)

    def hash_file(self, file_path: Path) -> str:
        if not file_path.exists():
            return ""
        return hashlib.sha256(file_path.read_bytes()).hexdigest()

    def rebuild_and_verify(self, seed: int, output_dir: Path) -> Tuple[bool, Dict[str, Any]]:
        """Regenerates tasks from seed and verifies identical file hashes."""
        commit_hash = "934813e4d421071a1b3db3973c02fe2721359a6e"
        try:
            from taskforge.adapters.python_adapter import PythonAdapter
            adapter = PythonAdapter(self.target_repo_path)
            c = adapter.get_commit_hash()
            if c:
                commit_hash = c
        except Exception:
            pass

        proposer1 = FeatureProposer(offline=True)
        proposals1 = proposer1.get_proposals(n=3, seed=seed)

        hashes_run1 = {}
        for p in proposals1:
            t_dir = self.packager.package(p, output_dir / "run1", commit_hash)
            hashes_run1[p.task_id] = {
                "instruction": self.hash_file(t_dir / "instruction.md"),
                "test": self.hash_file(t_dir / "tests" / "test_feature.py"),
                "solve": self.hash_file(t_dir / "solution" / "solve.sh")
            }

        proposer2 = FeatureProposer(seed=seed, offline=True)
        proposals2 = proposer2.get_proposals(n=3)
        hashes_run2 = {}
        for p in proposals2:
            t_dir = self.packager.package(p, output_dir / "run2", commit_hash)
            hashes_run2[p.task_id] = {
                "instruction": self.hash_file(t_dir / "instruction.md"),
                "test": self.hash_file(t_dir / "tests" / "test_feature.py"),
                "solve": self.hash_file(t_dir / "solution" / "solve.sh")
            }

        all_identical = (hashes_run1 == hashes_run2)
        return all_identical, {
            "seed": seed,
            "tasks_checked": list(hashes_run1.keys()),
            "bit_identical": all_identical
        }

