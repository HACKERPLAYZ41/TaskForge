#!/bin/bash
set -e

# TaskForge Reference Solution for: click-command-aliases
if [ -d "/workspace/repo" ]; then
    cd /workspace/repo
fi

python3 - << 'PYEOF'
import json
from pathlib import Path

p = Path('src/click/core.py')
content = p.read_text(encoding='utf-8')
edits = json.loads("[{\"target\": \"        deprecated: bool = False,\\n    ) -> None:\", \"replacement\": \"        deprecated: bool = False,\\n        aliases: t.Optional[t.Sequence[str]] = None,\\n    ) -> None:\"}, {\"target\": \"        super().__init__(name, context_settings)\", \"replacement\": \"        super().__init__(name, context_settings)\\n        self.aliases: t.List[str] = list(aliases) if aliases else []\"}, {\"target\": \"    def get_command(self, ctx: Context, cmd_name: str) -> t.Optional[Command]:\\n        return self.commands.get(cmd_name)\", \"replacement\": \"    def get_command(self, ctx: Context, cmd_name: str) -> t.Optional[Command]:\\n        cmd = self.commands.get(cmd_name)\\n        if cmd is not None:\\n            return cmd\\n        for c in self.commands.values():\\n            if cmd_name in getattr(c, 'aliases', ()):\\n                return c\\n        return None\"}]")
for item in edits:
    target = item['target']
    replacement = item['replacement']
    assert target in content, f'Search target not found in {p}'
    content = content.replace(target, replacement, 1)
p.write_text(content, encoding='utf-8')
PYEOF

