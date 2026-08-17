import platform
import subprocess
from pathlib import Path


def is_windows() -> bool:
    return platform.system() == "Windows"


def is_wsl() -> bool:
    return "microsoft" in platform.uname().release.lower()


def get_hooks_dir() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--git-path", "hooks"],
        capture_output=True,
        text=True,
        check=True,
    )
    return Path(result.stdout.strip())


def is_in_repo():
    result = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        capture_output=True, 
        text=True,
        check=False,
    )
    return result.returncode == 0 and result.stdout.strip() == "true"
