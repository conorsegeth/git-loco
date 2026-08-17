import subprocess
import sys

from rich.console import Console

from git_loco.platforms import windows
from git_loco.platforms.windows import LocationStatus
from git_loco.utils import is_windows, is_wsl

console = Console()


def get_location() -> None:
    console.print(r"[dim]\[git-loco][/dim]")

    if not (is_windows() or is_wsl()):
        console.print("[yellow]Location capture only supported on Windows/WSL.[/yellow]")
        return

    result = windows.get_location()



def main() -> None:
    args = sys.argv[1:]
    result = subprocess.run(["git"] + args, check=False)

    if result.returncode == 0 and "commit" in args:
        get_location()
        print("post-commit: done")
    elif result.returncode == 0 and "push" in args:
        get_location()
        print("post-push: done")

    sys.exit(result.returncode)


if __name__ == "__main__":
    main()