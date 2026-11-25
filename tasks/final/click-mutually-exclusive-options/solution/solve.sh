#!/bin/bash
set -e

# TaskForge Reference Solution for: click-mutually-exclusive-options
if [ -d "/workspace/repo" ]; then
    cd /workspace/repo
fi

python3 - << 'PYEOF'
import json
from pathlib import Path

p = Path('src/click/core.py')
content = p.read_text(encoding='utf-8')
edits = json.loads("[{\"target\": \"        show_envvar: bool = False,\\n        **attrs: t.Any,\\n    ) -> None:\", \"replacement\": \"        show_envvar: bool = False,\\n        mutually_exclusive: t.Optional[t.Sequence[str]] = None,\\n        **attrs: t.Any,\\n    ) -> None:\"}, {\"target\": \"        self.allow_from_autoenv = allow_from_autoenv\", \"replacement\": \"        self.allow_from_autoenv = allow_from_autoenv\\n        self.mutually_exclusive: t.List[str] = list(mutually_exclusive) if mutually_exclusive else []\"}, {\"target\": \"                if self.is_flag:\\n                    raise TypeError(\\\"'count' is not valid with 'is_flag'.\\\")\\n\\n    def to_info_dict(self) -> t.Dict[str, t.Any]:\", \"replacement\": \"                if self.is_flag:\\n                    raise TypeError(\\\"'count' is not valid with 'is_flag'.\\\")\\n\\n    def handle_parse_result(\\n        self, ctx: Context, opts: t.Mapping[str, t.Any], args: t.List[str]\\n    ) -> t.Tuple[t.Any, t.List[str]]:\\n        value, args = super().handle_parse_result(ctx, opts, args)\\n        if self.mutually_exclusive and ctx.get_parameter_source(self.name) not in (None, ParameterSource.DEFAULT):\\n            for mutex_name in self.mutually_exclusive:\\n                if mutex_name in ctx.params and ctx.get_parameter_source(mutex_name) not in (None, ParameterSource.DEFAULT):\\n                    raise UsageError(\\n                        f\\\"Option '{self.name}' is mutually exclusive with '{mutex_name}'.\\\"\\n                    )\\n        return value, args\\n\\n    def to_info_dict(self) -> t.Dict[str, t.Any]:\"}]")
for item in edits:
    target = item['target']
    replacement = item['replacement']
    assert target in content, f'Search target not found in {p}'
    content = content.replace(target, replacement, 1)
p.write_text(content, encoding='utf-8')
PYEOF

