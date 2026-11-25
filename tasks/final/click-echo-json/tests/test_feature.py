import json
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
