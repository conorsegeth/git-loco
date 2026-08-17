import subprocess
import sys

from rich.console import Console
from argparse import ArgumentParser

from git_loco.errors import LocationUnavailableError
from git_loco.platforms import windows
from git_loco.platforms.windows import LocationStatus
from git_loco.types import Coordinates
from git_loco.utils import is_windows, is_wsl, get_hooks_dir, is_in_repo

console = Console()

MARKER = "Installed by [git-loco]"
CAPTURE_CMD = "git-loco capture"
DISABLE_CMD = "git-loco disable"

HOOK_SCRIPT = f"""#!/bin/sh
# {MARKER}
# To uninstall, delete this file or run: {DISABLE_CMD}
{CAPTURE_CMD}
"""

def get_location() -> Coordinates:
    console.print(r"[dim]\[git-loco][/dim]")

    if not (is_windows() or is_wsl()):
        raise LocationUnavailableError("Location capture only supported on Windows/WSL.")

    return windows.get_location()



def cmd_enable():
    if not is_in_repo():
        console.print("[red]Not inside a git repository.[/red]")
        sys.exit(1)

    if not (is_windows() or is_wsl()):
        console.print("[red]Platform not supported.[/red]")
        sys.exit(1)

    hooks_dir = get_hooks_dir()
    hooks_dir.mkdir(parents=True, exist_ok=True)
    hook_path = hooks_dir / "post-commit"

    if hook_path.exists():
        existing = hook_path.read_text()
        if MARKER in existing:
            console.print("[yellow]git-loco hook already installed in this repo.[/yellow]")
            return

        console.print()
        console.print("A post-commit hook already exists at:")
        console.print(hook_path)
        console.print()
        console.print("To enable commit capture, add this line to it:")
        console.print(CAPTURE_CMD)
        console.print()
        return

    hook_path.write_text(HOOK_SCRIPT)
    hook_path.chmod(hook_path.stat().st_mode | 0o111)  # make the hook file executable

    console.print("\n\\[git-loco] enabled\n")


def cmd_disable():
    if not is_in_repo():
        console.print("[red]Not inside a git repository.[/red]")
        sys.exit(1)

    hooks_dir = get_hooks_dir()
    hook_path = hooks_dir / "post-commit"

    if not hook_path.exists():
        console.print("Disabled")
        return

    hook_text = hook_path.read_text()
    if MARKER not in hook_text:
        console.print()
        console.print(
               "To disable commit capture, remove "
               f"[white]\"{CAPTURE_CMD}\"[/white] from:\n"
               f"{hook_path}"
           )
        console.print()
        return

    hook_path.unlink()
    console.print("\n\\[git-loco] disabled\n")

def install_hooks():
    hooks_dir = get_hooks_dir()
    hooks_dir.mkdir(parents=True, exist_ok=True)



def cmd_capture():
    if not (is_windows() or is_wsl()):
        console.print("[red]Platform not supported.[/red]")
        sys.exit(1)
    
    try:
        loc = get_location()
        console.print(f"[green]coords: {loc}[/green]")
    except LocationUnavailableError as e:
        console.print(f"[yellow]{e}[/yellow]")
        console.print("post-commit: done (no location)")
        return



def main() -> None:
    parser = ArgumentParser(
        prog="git-loco",
        description="Capture commit location and metadata."
    )

    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("enable", help="install the post-commit hook")
    sub.add_parser("disable", help="remove the post-commit hook")
    sub.add_parser("capture", help="capture current location and commit metadata")

    args = parser.parse_args()

    if args.command == "enable": cmd_enable()
    if args.command == "disable": cmd_disable()
    if args.command == "capture": cmd_capture()

    # args = sys.argv[1:]
    # result = subprocess.run(["git"] + args, check=False)

    # if result.returncode == 0 and "commit" in args:
    #     get_location()
    #     print("post-commit: done")
    # elif result.returncode == 0 and "push" in args:
    #     get_location()
    #     print("post-push: done")

    # sys.exit(result.returncode)


if __name__ == "__main__":
    main()