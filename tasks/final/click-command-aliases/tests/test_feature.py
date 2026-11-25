import click
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
