import click
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
