import sys
from sqlite3 import OperationalError

import typer

from git_loco.database.store import CommitEntry, get_store
from git_loco.errors import LocationUnavailableError, NotInRepoError
from git_loco.platforms import windows
from git_loco.types import Coordinates
from git_loco.utils import git_metadata, is_in_repo, is_offline, is_windows, is_wsl


def get_location() -> Coordinates:
    if not (is_windows() or is_wsl()):
        raise LocationUnavailableError(
            "Location capture only supported on Windows/WSL."
        )

    return windows.get_location()


def capture():
    """Capture current location and latest commit metadata."""
    typer.echo("[git-loco] Capturing...")

    if not (is_windows() or is_wsl()):
        typer.echo("[git-loco] Platform not supported.", err=True)
        sys.exit(1)

    if not is_in_repo():
        raise NotInRepoError("Not inside a git repository.")

    meta = git_metadata()
    offline = is_offline()
    location = None

    if not offline:
        try:
            location = get_location()
        except LocationUnavailableError as e:
            typer.echo(f"[git-loco] {e}")

    commit_location = {
        "location_status": "success" if location else "failure",
        "location_source": "windows-geolocation" if location else None,
        "latitude": location.latitude if location else None,
        "longitude": location.longitude if location else None,
        "accuracy": location.accuracy if location else None,
        "offline": offline,
    }

    entry = CommitEntry(
        **meta,
        **commit_location,
    )

    store = get_store()
    try:
        store.save_commit(entry)
        typer.echo("[git-loco] Captured!")
    except OperationalError:
        typer.echo("[git-loco] Failed. Database error.", err=True)
    finally:
        store.close()
