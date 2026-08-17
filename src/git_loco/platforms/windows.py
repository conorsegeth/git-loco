import json
import subprocess
from enum import StrEnum
from json import JSONDecodeError
from pathlib import Path
from subprocess import SubprocessError

from rich.console import Console

from git_loco.utils import is_windows, is_wsl

console = Console()

SCRIPTS_DIR = Path(__file__).resolve().parents[3] / "scripts"


class LocationStatus(StrEnum):
    ENABLED = "ENABLED"
    POLICY_DISABLED = "POLICY_DISABLED"
    MASTER_DISABLED = "MASTER_DISABLED"
    APPS_DISABLED = "APPS_DISABLED"
    DESKTOP_DISABLED = "DESKTOP_DISABLED"
    UNKNOWN = "UNKNOWN"


DEFAULT_LOCATION_WARNING = (
    "Could not verify location permissions. Please check Windows Location Settings."
)

LOCATION_WARNING_MESSAGES: dict[LocationStatus, str] = {
    LocationStatus.POLICY_DISABLED: (
        "Location access is disabled by Group Policy. Contact your administrator."
    ),
    LocationStatus.MASTER_DISABLED: (
        "Location access is disabled because location services are OFF.\n"
        "To fix this, go to Settings → Privacy & security → Location and turn ON 'Location services'."
    ),
    LocationStatus.APPS_DISABLED: (
        "Location access is disabled for apps.\n"
        "To fix this, go to Settings → Privacy & security → Location and turn ON 'Let apps access your location'."
    ),
    LocationStatus.DESKTOP_DISABLED: (
        "Location access is disabled for desktop apps.\n"
        "To fix this, go to Settings → Privacy & security → Location and turn ON 'Let desktop apps access your location'."
    ),
}


def _get_warning_text(status: LocationStatus) -> str:
    return LOCATION_WARNING_MESSAGES.get(status, DEFAULT_LOCATION_WARNING)


# def show_location_warning(status: LocationStatus) -> None:
#     """Prints the formatted location warning message to the console."""
#     msg = get_location_warning_text(status)
#     console.print(f"[red]{msg}[/red]")


def _get_location_status() -> LocationStatus:
    script_path = SCRIPTS_DIR / "location-enabled.ps1"
    try:
        ps = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(script_path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        try:
            return LocationStatus(ps.stdout.strip())
        except ValueError:
            return LocationStatus.UNKNOWN
    except (SubprocessError, OSError):
        return LocationStatus.UNKNOWN


def _get_coordinates() -> dict | None:
    script_path = SCRIPTS_DIR / "get-location.ps1"
    try:
        ps = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(script_path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        output = ps.stdout.strip()
        if output:
            return json.loads(output)
    except (SubprocessError, OSError, JSONDecodeError) as e:
        return {"error": str(e)}
    return None


def get_location() -> dict:
    if not (is_windows() or is_wsl()):
        return {
            "ok": False,
            "message": "Location capture only supported on Windows/WSL.",
        }

    status = _get_location_status()
    if status is not LocationStatus.ENABLED:
        return {
            "ok": False,
            "message": _get_warning_text(status),
        }

    coords = _get_coordinates()
    if not coords or "error" in coords:
        return {
            "ok": False,
            "message": (
                coords.get("error", "Failed to retrieve coordinates.") if coords else "No location data returned."
            ),
        }

    lat = coords.get("Latitude")
    long = coords.get("Longitude")
    accuracy = coords.get("Accuracy")

    return {
        "ok": True, 
        "latitude": lat,
        "longitude": long,
        "accuracy": accuracy
    }
