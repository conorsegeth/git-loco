import sys
from typing import Annotated

import typer

from git_loco.config import (
    ConfigError,
    clear_provider_config,
    config_path,
    load_provider_config,
    save_provider_config,
)
from git_loco.database.providers import PROVIDERS, get_provider
from git_loco.errors import ProviderError

config_app = typer.Typer(help="Show or update provider configuration.")

SECRET_KEYS = ("token", "secret", "password")


def _masked_prompt(prompt: str) -> str:
    """Prompt for a secret, echoing '*' per character.

    Uses cbreak-style mode with ISIG off so Ctrl+C arrives as a plain byte
    (\x03) that we handle ourselves — deterministic, and the terminal is
    always restored. pwinput sets raw mode and swallows Ctrl+C entirely.
    Falls back to plain input() when stdin is not a terminal (pipes/scripts).
    Arrow keys not handled (ponytail).
    """
    if not sys.stdin.isatty():
        return input(prompt)

    sys.stdout.write(prompt)
    sys.stdout.flush()
    chars: list[str] = []
    try:
        if sys.platform == "win32":
            import msvcrt

            while True:
                ch = msvcrt.getwch()
                if ch in ("\r", "\n"):
                    break
                if ch in ("\b", "\x7f"):
                    if chars:
                        chars.pop()
                        sys.stdout.write("\b \b")
                elif ch == "\x03":
                    raise KeyboardInterrupt
                else:
                    chars.append(ch)
                    sys.stdout.write("*")
                sys.stdout.flush()
        else:
            import termios

            fd = sys.stdin.fileno()
            old = termios.tcgetattr(fd)
            try:
                new = termios.tcgetattr(fd)
                new[3] &= ~(termios.ECHO | termios.ICANON | termios.ISIG)
                termios.tcsetattr(fd, termios.TCSADRAIN, new)
                while True:
                    ch = sys.stdin.read(1)
                    if ch in ("\r", "\n"):
                        break
                    if ch in ("\b", "\x7f"):
                        if chars:
                            chars.pop()
                            sys.stdout.write("\b \b")
                    elif ch == "\x03":
                        raise KeyboardInterrupt
                    else:
                        chars.append(ch)
                        sys.stdout.write("*")
                    sys.stdout.flush()
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old)
    finally:
        sys.stdout.write("\n")
        sys.stdout.flush()
    return "".join(chars)


@config_app.command("set")
def config_set(provider: str):
    """Save config for a provider."""
    try:
        provider_cls = get_provider(provider)
    except ProviderError as e:
        typer.echo(f"{e}", err=True)
        sys.exit(1)

    current = load_provider_config(provider_cls) or {}
    values = {}
    for key in provider_cls.config_keys:
        existing = current.get(key)
        if key in SECRET_KEYS:
            prompt = (
                f"{key}: " if not existing else f"{key} [{'*' * len(existing)}]: "
            )
            values[key] = _masked_prompt(prompt) or existing or ""
        else:
            values[key] = typer.prompt(key, default=existing, show_default=True)

    try:
        save_provider_config(provider_cls.name, values)
    except (ConfigError, OSError) as e:
        typer.echo(f"{e}", err=True)
        typer.echo(f"Recovery: delete {config_path()} and rerun this command.")
        sys.exit(1)

    typer.echo(f"{provider} config saved.")


@config_app.command("show")
def config_show(
    provider: Annotated[
        str | None, typer.Argument(help="provider name (default: all)")
    ] = None,
):
    """Show current config for a provider."""
    if provider is not None:
        try:
            provider_cls = get_provider(provider)
        except ProviderError as e:
            typer.echo(f"{e}", err=True)
            sys.exit(1)
        targets = [(provider, provider_cls)]
    else:
        targets = list(PROVIDERS.items())

    typer.echo(f"Config file: {config_path()}")
    for name, cls in targets:
        config = load_provider_config(cls)
        if config is None:
            typer.echo(f"{name}: not configured")
        else:
            typer.echo(f"{name}: configured")
            for key, value in config.items():
                shown = "*" * len(value) if key in SECRET_KEYS else value
                typer.echo(f"  {key}: {shown}")


@config_app.command("clear")
def config_clear(provider: str):
    """Remove config for a provider."""
    try:
        provider_cls = get_provider(provider)
    except ProviderError as e:
        typer.echo(f"{e}", err=True)
        sys.exit(1)

    try:
        clear_provider_config(provider_cls.name)
    except (ConfigError, OSError) as e:
        typer.echo(f"{e}", err=True)
        typer.echo(f"Recovery: delete {config_path()} and rerun this command.")
        sys.exit(1)

    typer.echo(f"{provider} config cleared.")
