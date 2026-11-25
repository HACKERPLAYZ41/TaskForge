#!/bin/bash
set -e

# TaskForge Reference Solution for: click-dynamic-choice-callback
if [ -d "/workspace/repo" ]; then
    cd /workspace/repo
fi

python3 - << 'PYEOF'
import json
from pathlib import Path

p = Path('src/click/types.py')
content = p.read_text(encoding='utf-8')
target = json.loads("\"    def __init__(self, choices: t.Sequence[str], case_sensitive: bool = True) -> None:\\n        self.choices = choices\\n        self.case_sensitive = case_sensitive\"")
replacement = json.loads("\"    def __init__(\\n        self,\\n        choices: t.Union[t.Sequence[str], t.Callable[[], t.Sequence[str]]],\\n        case_sensitive: bool = True,\\n    ) -> None:\\n        if callable(choices):\\n            self._choices_callback: t.Optional[t.Callable[[], t.Sequence[str]]] = choices\\n            self._choices: t.Optional[t.List[str]] = None\\n        else:\\n            self._choices_callback = None\\n            self._choices = list(choices)\\n        self.case_sensitive = case_sensitive\\n\\n    @property\\n    def choices(self) -> t.Sequence[str]:\\n        if self._choices_callback is not None:\\n            return list(self._choices_callback())\\n        return self._choices or []\\n\\n    @choices.setter\\n    def choices(self, value: t.Sequence[str]) -> None:\\n        self._choices = list(value)\\n        self._choices_callback = None\"")
assert target in content, f'Search target not found in {p}'
content = content.replace(target, replacement, 1)
p.write_text(content, encoding='utf-8')
PYEOF

