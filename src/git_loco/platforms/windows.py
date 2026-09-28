import json
import stat
import subprocess
from enum import StrEnum
from json import JSONDecodeError
from pathlib import Path
from subprocess import SubprocessError

from git_loco.errors import LocationUnavailableError
from git_loco.types import Coordinates

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"


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


def _get_location_status() -> LocationStatus:
    script_path = SCRIPTS_DIR / "location-enabled.ps1"
    if not script_path.exists():
        raise LocationUnavailableError("git-loco scripts not found. Try reinstalling.")

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
    if not script_path.exists():
        raise LocationUnavailableError("git-loco scripts not found. Try reinstalling.")
    
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


def get_location() -> Coordinates:
    status = _get_location_status()
    if status is not LocationStatus.ENABLED:
        raise LocationUnavailableError(_get_warning_text(status))

    coords = _get_coordinates()
    if not coords:
        raise LocationUnavailableError("Failed to fetch location data.")

    if "error" in coords:
        raise LocationUnavailableError(coords.get("error"))

    status = coords.get("Status")
    if status != "Success":
        raise LocationUnavailableError("Failed to fetch location data.")

    lat = coords.get("Latitude")
    long = coords.get("Longitude")
    acc = coords.get("Accuracy")

    return Coordinates(latitude=lat, longitude=long, accuracy=acc)
