import click
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
