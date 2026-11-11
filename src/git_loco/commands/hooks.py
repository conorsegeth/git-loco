import sys

import typer

from git_loco.config import APP_NAME
from git_loco.utils import get_hooks_dir, is_in_repo, is_windows, is_wsl

hook_app = typer.Typer(help="Manage the post-commit git hook.")

MARKER = f"Installed by {APP_NAME}"
CAPTURE_CMD = f"{APP_NAME} capture"
UNINSTALL_CMD = f"{APP_NAME} hook uninstall"

HOOK_SCRIPT = f"""#!/bin/sh
# {MARKER}
# To uninstall, delete this file or run: {UNINSTALL_CMD}
{CAPTURE_CMD}
"""


@hook_app.command()
def install():
    """Install the post-commit hook."""
    if not is_in_repo():
        typer.echo("Not inside a git repository.", err=True)
        sys.exit(1)

    if not (is_windows() or is_wsl()):
        typer.echo("Platform not supported.", err=True)
        sys.exit(1)

    hooks_dir = get_hooks_dir()
    hooks_dir.mkdir(parents=True, exist_ok=True)
    hook_path = hooks_dir / "post-commit"

    if hook_path.exists():
        existing = hook_path.read_text()
        if MARKER in existing:
            typer.echo("git-loco hook already installed in this repo.")
            return

        typer.echo(f"A post-commit hook already exists at: {hook_path}")
        typer.echo(f"To install commit capture, add this line to it: {CAPTURE_CMD}")
        return

    hook_path.write_text(HOOK_SCRIPT)
    hook_path.chmod(hook_path.stat().st_mode | 0o111)  # make the hook file executable

    typer.echo("installed")


@hook_app.command()
def uninstall():
    """Remove the post-commit hook."""
    if not is_in_repo():
        typer.echo("Not inside a git repository.", err=True)
        sys.exit(1)

    hooks_dir = get_hooks_dir()
    hook_path = hooks_dir / "post-commit"

    if not hook_path.exists():
        typer.echo("uninstalled")
        return

    hook_text = hook_path.read_text()
    if MARKER not in hook_text:
        typer.echo(f"To uninstall commit capture, remove '{CAPTURE_CMD}' from: {hook_path}")
        return

    hook_path.unlink()
    typer.echo("uninstalled")
