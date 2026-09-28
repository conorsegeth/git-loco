import typer

from git_loco.commands.capture import capture
from git_loco.commands.config import config_app
from git_loco.commands.hooks import hook_app
from git_loco.commands.sync import providers, sync

app = typer.Typer(help="Capture commit location and metadata.")
app.command()(capture)
app.command()(sync)
app.command()(providers)
app.add_typer(hook_app, name="hook")
app.add_typer(config_app, name="config")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
