"""Configuration loader for TaskForge."""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional
import os
import yaml

@dataclass
class TaskForgeConfig:
    repo_path: Path
    language: str = "python"
    test_command: str = "pytest -q"
    python_version: str = "3.12"
    seed: int = 42
    generator_version: str = "1.0.0"
    repo_identifier: str = "pallets/click"
    repo_url: str = "https://github.com/pallets/click.git"
    base_commit: str = "934813e4d421071a1b3db3973c02fe2721359a6e"
    version_tag: str = "8.1.8"
    license: str = "BSD-3-Clause"
    harbor_version: str = "0.25.0"
    docker_base_image: str = "python:3.12-slim-bookworm"
    docker_image_tag: str = "taskforge-click-baseline:8.1.8"
    provider: Dict[str, Any] = field(default_factory=lambda: {
        "name": "openrouter",
        "api_key_env": "OPENROUTER_API_KEY",
        "call_delay_sec": 1.5,
        "cache_dir": ".cache/llm"
    })
    roles: Dict[str, Any] = field(default_factory=dict)
    models: Dict[str, str] = field(default_factory=dict)
    raw_config: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "TaskForgeConfig":
        if config_path is None:
            config_path = Path.home() / "taskforge" / "config.yaml"
        if not config_path.exists():
            return cls(repo_path=Path.home() / "taskforge" / ".cache" / "click_repo")

        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        repo_str = data.get("repo_path", "~/.cache/click_repo")
        repo_path = Path(os.path.expanduser(repo_str)).resolve()

        return cls(
            repo_path=repo_path,
            language=data.get("language", "python"),
            test_command=data.get("test_command", "pytest -q"),
            python_version=str(data.get("python_version", "3.12")),
            seed=int(data.get("seed", 42)),
            generator_version=str(data.get("generator_version", "1.0.0")),
            repo_identifier=data.get("repo_identifier", "pallets/click"),
            repo_url=data.get("repo_url", "https://github.com/pallets/click.git"),
            base_commit=data.get("base_commit", "934813e4d421071a1b3db3973c02fe2721359a6e"),
            version_tag=data.get("version_tag", "8.1.8"),
            license=data.get("license", "BSD-3-Clause"),
            harbor_version=data.get("harbor_version", "0.25.0"),
            docker_base_image=data.get("docker_base_image", "python:3.12-slim-bookworm"),
            docker_image_tag=data.get("docker_image_tag", "taskforge-click-baseline:8.1.8"),
            provider=data.get("provider", {}),
            roles=data.get("roles", {}),
            models=data.get("models", {}),
            raw_config=data
        )
