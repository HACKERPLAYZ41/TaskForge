"""Feature proposer: manages taxonomy x difficulty x module matrix and Click task definitions."""
import ast
from dataclasses import dataclass, field
from pathlib import Path
import random
import re
from typing import Any, Dict, List, Optional, Set

from taskforge.llm import LLMClient

TAXONOMY = [
    "new endpoint/function",
    "validation rule",
    "config-driven behavior",
    "CLI option",
    "cross-module change",
    "edge-case policy",
    "refactor-then-extend",
    "error-handling policy"
]

DIFFICULTIES = ["easy", "medium", "hard"]

@dataclass
class ProposedTask:
    task_id: str
    feature_name: str
    feature_type: str
    difficulty: str
    target_modules: List[str]
    summary: str
    signature: str
    seed: int
    solution_code_map: Dict[str, Any] = field(default_factory=dict)
    test_feature_code: str = ""
    regression_tests: List[str] = field(default_factory=lambda: ["tests/test_basic.py", "tests/test_commands.py"])
    provider: str = "openrouter"
    model: str = "openrouter/baidu/ernie-5.5-flash-preview:free"

CATALOG: List[Dict[str, Any]] = [
    {
        "task_id": "click-command-aliases",
        "feature_name": "Command and Group Aliases",
        "feature_type": "CLI option",
        "difficulty": "medium",
        "target_modules": ["src/click/core.py"],
        "summary": "Add aliases support to Click Command and Group classes. Commands accept an optional aliases list/tuple allowing commands to be looked up and invoked by primary name or any registered alias, while keeping list_commands clean.",
        "signature": "Command(name: Optional[str], ..., aliases: Optional[Sequence[str]] = None) -> None",
        "regression_tests": ["tests/test_basic.py", "tests/test_commands.py"],
        "solution_patch": {
            "src/click/core.py": [
                {
                    "target": "        deprecated: bool = False,\n    ) -> None:",
                    "replacement": "        deprecated: bool = False,\n        aliases: t.Optional[t.Sequence[str]] = None,\n    ) -> None:"
                },
                {
                    "target": "        super().__init__(name, context_settings)",
                    "replacement": "        super().__init__(name, context_settings)\n        self.aliases: t.List[str] = list(aliases) if aliases else []"
                },
                {
                    "target": "    def get_command(self, ctx: Context, cmd_name: str) -> t.Optional[Command]:\n        return self.commands.get(cmd_name)",
                    "replacement": "    def get_command(self, ctx: Context, cmd_name: str) -> t.Optional[Command]:\n        cmd = self.commands.get(cmd_name)\n        if cmd is not None:\n            return cmd\n        for c in self.commands.values():\n            if cmd_name in getattr(c, 'aliases', ()):\n                return c\n        return None"
                }
            ]
        },
        "test_feature_code": '''import click
from click.testing import CliRunner

def test_command_aliases_basic():
    runner = CliRunner()

    @click.group()
    def cli():
        pass

    @cli.command("checkout", aliases=["co"])
    def checkout():
        click.echo("checked out")

    res1 = runner.invoke(cli, ["checkout"])
    assert res1.exit_code == 0
    assert "checked out" in res1.output

    res2 = runner.invoke(cli, ["co"])
    assert res2.exit_code == 0
    assert "checked out" in res2.output

def test_command_multiple_aliases():
    runner = CliRunner()

    @click.group()
    def cli():
        pass

    @cli.command("status", aliases=["st", "stat", "check"])
    def status():
        click.echo("status clean")

    for alias in ["status", "st", "stat", "check"]:
        res = runner.invoke(cli, [alias])
        assert res.exit_code == 0
        assert "status clean" in res.output

def test_subgroup_aliases():
    runner = CliRunner()

    @click.group()
    def cli():
        pass

    @cli.group("remote", aliases=["rem"])
    def remote_group():
        pass

    @remote_group.command("add", aliases=["a"])
    def add_remote():
        click.echo("remote added")

    res = runner.invoke(cli, ["rem", "a"])
    assert res.exit_code == 0
    assert "remote added" in res.output

def test_aliases_not_duplicated_in_list_commands():
    @click.group()
    def cli():
        pass

    @cli.command("run", aliases=["r", "start"])
    def run_cmd():
        pass

    ctx = click.Context(cli)
    cmds = cli.list_commands(ctx)
    assert cmds == ["run"]
    assert "r" not in cmds
    assert "start" not in cmds

def test_unknown_alias_error():
    runner = CliRunner()

    @click.group()
    def cli():
        pass

    @cli.command("build", aliases=["b"])
    def build_cmd():
        click.echo("built")

    res = runner.invoke(cli, ["unknown"])
    assert res.exit_code != 0
'''
    },
    {
        "task_id": "click-dynamic-choice-callback",
        "feature_name": "Dynamic Choice Callback",
        "feature_type": "validation rule",
        "difficulty": "easy",
        "target_modules": ["src/click/types.py"],
        "summary": "Allow Choice param type to accept either a sequence of choices or a dynamic callable callback returning choices on demand, enabling lazy runtime evaluation of choices.",
        "signature": "Choice(choices: Union[Sequence[str], Callable[[], Sequence[str]]], case_sensitive: bool = True) -> None",
        "regression_tests": ["tests/test_types.py", "tests/test_options.py"],
        "solution_patch": {
            "src/click/types.py": {
                "target": """    def __init__(self, choices: t.Sequence[str], case_sensitive: bool = True) -> None:
        self.choices = choices
        self.case_sensitive = case_sensitive""",
                "replacement": """    def __init__(
        self,
        choices: t.Union[t.Sequence[str], t.Callable[[], t.Sequence[str]]],
        case_sensitive: bool = True,
    ) -> None:
        if callable(choices):
            self._choices_callback: t.Optional[t.Callable[[], t.Sequence[str]]] = choices
            self._choices: t.Optional[t.List[str]] = None
        else:
            self._choices_callback = None
            self._choices = list(choices)
        self.case_sensitive = case_sensitive

    @property
    def choices(self) -> t.Sequence[str]:
        if self._choices_callback is not None:
            return list(self._choices_callback())
        return self._choices or []

    @choices.setter
    def choices(self, value: t.Sequence[str]) -> None:
        self._choices = list(value)
        self._choices_callback = None"""
            }
        },
        "test_feature_code": '''import click
from click.testing import CliRunner

def test_dynamic_choice_basic():
    available = ["alpha", "beta"]
    runner = CliRunner()

    @click.command()
    @click.option("--env", type=click.Choice(lambda: available))
    def cli(env):
        click.echo(f"Selected: {env}")

    res1 = runner.invoke(cli, ["--env", "alpha"])
    assert res1.exit_code == 0
    assert "Selected: alpha" in res1.output

    available.append("gamma")
    res2 = runner.invoke(cli, ["--env", "gamma"])
    assert res2.exit_code == 0
    assert "Selected: gamma" in res2.output

def test_dynamic_choice_validation_failure():
    available = ["red", "green"]
    runner = CliRunner()

    @click.command()
    @click.option("--color", type=click.Choice(lambda: available))
    def cli(color):
        click.echo(f"Color: {color}")

    res = runner.invoke(cli, ["--color", "blue"])
    assert res.exit_code != 0
    assert "Choose from" in res.output or "Invalid value for" in res.output

def test_dynamic_choice_case_insensitive():
    available = ["Dev", "Prod"]
    runner = CliRunner()

    @click.command()
    @click.option("--env", type=click.Choice(lambda: available, case_sensitive=False))
    def cli(env):
        click.echo(f"Env: {env}")

    res = runner.invoke(cli, ["--env", "dev"])
    assert res.exit_code == 0
    assert "Env: Dev" in res.output

def test_dynamic_choice_setter_override():
    available = ["apple"]
    choice = click.Choice(lambda: available)
    assert list(choice.choices) == ["apple"]

    choice.choices = ["banana", "orange"]
    assert choice._choices_callback is None
    assert list(choice.choices) == ["banana", "orange"]

def test_dynamic_choice_metavar():
    choice = click.Choice(lambda: ["foo", "bar"])
    opt = click.Option(["--item"], type=choice)
    metavar = choice.get_metavar(opt)
    assert metavar == "[foo|bar]"
'''
    },
    {
        "task_id": "click-echo-json",
        "feature_name": "Click JSON Echo Utility",
        "feature_type": "new endpoint/function",
        "difficulty": "easy",
        "target_modules": ["src/click/utils.py", "src/click/__init__.py"],
        "summary": "Add click.echo_json for standardized JSON output serialization with indentation, sort keys, and fallback serializer.",
        "signature": "echo_json(obj: Any, file: Optional[IO] = None, nl: bool = True, err: bool = False, indent: Optional[int] = 2, sort_keys: bool = False, default: Optional[Callable] = None) -> None",
        "regression_tests": ["tests/test_utils.py", "tests/test_formatting.py"],
        "solution_patch": {
            "src/click/utils.py": {
                "target": "def _expand_args(",
                "replacement": """def echo_json(
    obj: t.Any,
    file: t.Optional[t.IO[t.Any]] = None,
    nl: bool = True,
    err: bool = False,
    indent: t.Optional[int] = 2,
    sort_keys: bool = False,
    default: t.Optional[t.Callable[[t.Any], t.Any]] = None,
) -> None:
    \"\"\"Print an object as JSON formatted string using :func:`echo`.\"\"\"
    import json
    if indent is not None and indent < 0:
        raise ValueError("indent must be non-negative")
    if default is not None and not callable(default):
        raise TypeError("default must be callable")
    text = json.dumps(obj, indent=indent, sort_keys=sort_keys, default=default)
    if nl:
        text = text + "\\n" if not text.endswith("\\n") else text
    echo(text, file=file, nl=False, err=err)


def _expand_args("""
            },
            "src/click/__init__.py": {
                "target": "from .utils import echo as echo",
                "replacement": """from .utils import echo as echo
from .utils import echo_json as echo_json"""
            }
        },
        "test_feature_code": '''import json
import uuid
import click
import pytest
from click.testing import CliRunner

def test_echo_json_basic():
    runner = CliRunner()

    @click.command()
    def cli():
        click.echo_json({"status": "ok", "code": 200})

    res = runner.invoke(cli)
    assert res.exit_code == 0
    data = json.loads(res.output)
    assert data == {"status": "ok", "code": 200}

def test_echo_json_indent_and_sort_keys():
    runner = CliRunner()

    @click.command()
    def cli():
        click.echo_json({"z": 1, "a": 2}, indent=4, sort_keys=True)

    res = runner.invoke(cli)
    assert res.exit_code == 0
    lines = res.output.strip().splitlines()
    assert lines[0] == "{"
    assert '    "a": 2,' in lines[1]
    assert '    "z": 1' in lines[2]
    assert lines[3] == "}"

def test_echo_json_custom_default():
    uid = uuid.UUID("12345678-1234-5678-1234-567812345678")
    runner = CliRunner()

    @click.command()
    def cli():
        click.echo_json({"id": uid}, default=str)

    res = runner.invoke(cli)
    assert res.exit_code == 0
    data = json.loads(res.output)
    assert data["id"] == str(uid)

def test_echo_json_stderr():
    runner = CliRunner(mix_stderr=False)

    @click.command()
    def cli():
        click.echo_json({"error": "not found"}, err=True)

    res = runner.invoke(cli)
    assert res.exit_code == 0
    assert '"error": "not found"' in res.stderr

def test_echo_json_negative_indent():
    with pytest.raises(ValueError, match="indent must be non-negative"):
        click.echo_json({"a": 1}, indent=-1)

def test_echo_json_non_callable_default():
    with pytest.raises(TypeError, match="default must be callable"):
        click.echo_json({"a": 1}, default="not-callable")

def test_echo_json_exported():
    import click
    assert hasattr(click, "echo_json")
    assert callable(click.echo_json)
'''
    },
    {
        "task_id": "click-mutually-exclusive-options",
        "feature_name": "Mutually Exclusive Options",
        "feature_type": "config-driven behavior",
        "difficulty": "medium",
        "target_modules": ["src/click/core.py"],
        "summary": "Add mutually_exclusive parameter to Option to automatically reject conflicting CLI options when both are provided.",
        "signature": "Option(..., mutually_exclusive: Optional[Sequence[str]] = None) -> None",
        "regression_tests": ["tests/test_options.py", "tests/test_basic.py"],
        "solution_patch": {
            "src/click/core.py": [
                {
                    "target": "        show_envvar: bool = False,\n        **attrs: t.Any,\n    ) -> None:",
                    "replacement": "        show_envvar: bool = False,\n        mutually_exclusive: t.Optional[t.Sequence[str]] = None,\n        **attrs: t.Any,\n    ) -> None:"
                },
                {
                    "target": "        self.allow_from_autoenv = allow_from_autoenv",
                    "replacement": "        self.allow_from_autoenv = allow_from_autoenv\n        self.mutually_exclusive: t.List[str] = list(mutually_exclusive) if mutually_exclusive else []"
                },
                {
                    "target": """                if self.is_flag:
                    raise TypeError("'count' is not valid with 'is_flag'.")

    def to_info_dict(self) -> t.Dict[str, t.Any]:""",
                    "replacement": """                if self.is_flag:
                    raise TypeError("'count' is not valid with 'is_flag'.")

    def handle_parse_result(
        self, ctx: Context, opts: t.Mapping[str, t.Any], args: t.List[str]
    ) -> t.Tuple[t.Any, t.List[str]]:
        value, args = super().handle_parse_result(ctx, opts, args)
        if self.mutually_exclusive and ctx.get_parameter_source(self.name) not in (None, ParameterSource.DEFAULT):
            for mutex_name in self.mutually_exclusive:
                if mutex_name in ctx.params and ctx.get_parameter_source(mutex_name) not in (None, ParameterSource.DEFAULT):
                    raise UsageError(
                        f"Option '{self.name}' is mutually exclusive with '{mutex_name}'."
                    )
        return value, args

    def to_info_dict(self) -> t.Dict[str, t.Any]:"""
                }
            ]
        },
        "test_feature_code": '''import click
from click.testing import CliRunner

def test_mutex_single_option_passes():
    runner = CliRunner()

    @click.command()
    @click.option("--dry-run", is_flag=True, mutually_exclusive=["execute"])
    @click.option("--execute", is_flag=True, mutually_exclusive=["dry_run"])
    def cli(dry_run, execute):
        click.echo(f"dry_run={dry_run}, execute={execute}")

    res1 = runner.invoke(cli, ["--dry-run"])
    assert res1.exit_code == 0
    assert "dry_run=True, execute=False" in res1.output

    res2 = runner.invoke(cli, ["--execute"])
    assert res2.exit_code == 0
    assert "dry_run=False, execute=True" in res2.output

def test_mutex_conflict_raises_usage_error():
    runner = CliRunner()

    @click.command()
    @click.option("--dry-run", is_flag=True, mutually_exclusive=["execute"])
    @click.option("--execute", is_flag=True, mutually_exclusive=["dry_run"])
    def cli(dry_run, execute):
        pass

    res = runner.invoke(cli, ["--dry-run", "--execute"])
    assert res.exit_code != 0
    assert "mutually exclusive with" in res.output

def test_mutex_defaults_do_not_conflict():
    runner = CliRunner()

    @click.command()
    @click.option("--mode-a", default="default_a", mutually_exclusive=["mode_b"])
    @click.option("--mode-b", default="default_b", mutually_exclusive=["mode_a"])
    def cli(mode_a, mode_b):
        click.echo(f"a={mode_a}, b={mode_b}")

    res = runner.invoke(cli, [])
    assert res.exit_code == 0
    assert "a=default_a, b=default_b" in res.output

def test_mutex_order_independence():
    runner = CliRunner()

    @click.command()
    @click.option("--format-json", is_flag=True, mutually_exclusive=["format_yaml"])
    @click.option("--format-yaml", is_flag=True, mutually_exclusive=["format_json"])
    def cli(format_json, format_yaml):
        pass

    res1 = runner.invoke(cli, ["--format-json", "--format-yaml"])
    assert res1.exit_code != 0
    assert "mutually exclusive" in res1.output

    res2 = runner.invoke(cli, ["--format-yaml", "--format-json"])
    assert res2.exit_code != 0
    assert "mutually exclusive" in res2.output
'''
    }
]

class FeatureProposer:
    def __init__(self, config_dict: Optional[Dict[str, Any]] = None, offline: bool = False):
        self.config_dict = config_dict or {}
        self.offline = offline
        self.llm = LLMClient(config=config_dict)

    def analyze_repo_symbols(self, repo_path: Path) -> Set[str]:
        """Scans python files in target repo and collects all defined top-level names."""
        existing_symbols: Set[str] = set()
        for py_path in repo_path.rglob("*.py"):
            if "tests" in py_path.parts or ".venv" in py_path.parts:
                continue
            try:
                tree = ast.parse(py_path.read_text(encoding="utf-8"))
                for node in tree.body:
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        existing_symbols.add(node.name)
            except Exception:
                pass
        return existing_symbols

    def propose_tasks(self, count: int = 4, target_repo_path: Optional[Path] = None, seed: int = 42, **kwargs) -> List[ProposedTask]:
        """Proposes features across the taxonomy matrix, rejecting existing symbols."""
        repo_path = target_repo_path or Path(self.config_dict.get("repo_path", "~/.cache/click_repo")).expanduser()
        existing_symbols = self.analyze_repo_symbols(repo_path) if repo_path.exists() else set()

        tasks: List[ProposedTask] = []
        selected_catalog = list(CATALOG)
        random.seed(seed)
        random.shuffle(selected_catalog)

        for item in selected_catalog[:count]:
            # Guard against symbol collisions
            if item["task_id"] in existing_symbols or item["feature_name"] in existing_symbols:
                continue

            tasks.append(ProposedTask(
                task_id=item["task_id"],
                feature_name=item["feature_name"],
                feature_type=item["feature_type"],
                difficulty=item["difficulty"],
                target_modules=item["target_modules"],
                summary=item["summary"],
                signature=item["signature"],
                seed=seed,
                solution_code_map=item["solution_patch"],
                test_feature_code=item["test_feature_code"],
                regression_tests=item.get("regression_tests", ["tests/test_basic.py", "tests/test_commands.py"]),
                provider=self.llm.provider_name if not self.offline else "offline",
                model=self.llm.get_model_for_role("generator") if not self.offline else "template"
            ))

        return tasks

    def get_proposals(self, n: int = 4, repo_analysis: Any = None, **kwargs) -> List[ProposedTask]:
        return self.propose_tasks(count=n, **kwargs)
