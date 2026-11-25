"""Abstract base class for repository adapters."""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Tuple

class RepoAdapter(ABC):
    def __init__(self, repo_path: Path):
        self.repo_path = Path(repo_path).resolve()

    @abstractmethod
    def get_commit_hash(self) -> str:
        """Returns starting commit or repository version hash."""
        pass

    @abstractmethod
    def list_modules(self) -> List[Path]:
        """Lists source code files in repository."""
        pass

    @abstractmethod
    def list_tests(self) -> List[Path]:
        """Lists test files in repository."""
        pass

    @abstractmethod
    def run_tests(self, test_cmd: Optional[str] = None, cwd: Optional[Path] = None) -> Tuple[bool, str]:
        """Executes test suite and returns (success, combined_output)."""
        pass

    @abstractmethod
    def apply_patch(self, patch_diff: str, target_dir: Optional[Path] = None) -> bool:
        """Applies unified diff patch to repository."""
        pass
