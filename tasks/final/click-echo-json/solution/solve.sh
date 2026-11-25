#!/bin/bash
set -e

# TaskForge Reference Solution for: click-echo-json
if [ -d "/workspace/repo" ]; then
    cd /workspace/repo
fi

python3 - << 'PYEOF'
import json
from pathlib import Path

p = Path('src/click/utils.py')
content = p.read_text(encoding='utf-8')
target = json.loads("\"def _expand_args(\"")
replacement = json.loads("\"def echo_json(\\n    obj: t.Any,\\n    file: t.Optional[t.IO[t.Any]] = None,\\n    nl: bool = True,\\n    err: bool = False,\\n    indent: t.Optional[int] = 2,\\n    sort_keys: bool = False,\\n    default: t.Optional[t.Callable[[t.Any], t.Any]] = None,\\n) -> None:\\n    \\\"\\\"\\\"Print an object as JSON formatted string using :func:`echo`.\\\"\\\"\\\"\\n    import json\\n    if indent is not None and indent < 0:\\n        raise ValueError(\\\"indent must be non-negative\\\")\\n    if default is not None and not callable(default):\\n        raise TypeError(\\\"default must be callable\\\")\\n    text = json.dumps(obj, indent=indent, sort_keys=sort_keys, default=default)\\n    if nl:\\n        text = text + \\\"\\\\n\\\" if not text.endswith(\\\"\\\\n\\\") else text\\n    echo(text, file=file, nl=False, err=err)\\n\\n\\ndef _expand_args(\"")
assert target in content, f'Search target not found in {p}'
content = content.replace(target, replacement, 1)
p.write_text(content, encoding='utf-8')
PYEOF

python3 - << 'PYEOF'
import json
from pathlib import Path

p = Path('src/click/__init__.py')
content = p.read_text(encoding='utf-8')
target = json.loads("\"from .utils import echo as echo\"")
replacement = json.loads("\"from .utils import echo as echo\\nfrom .utils import echo_json as echo_json\"")
assert target in content, f'Search target not found in {p}'
content = content.replace(target, replacement, 1)
p.write_text(content, encoding='utf-8')
PYEOF

