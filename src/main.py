import json
import os
import subprocess
import sys

from rich.console import Console

console = Console()


def get_location():
    console.print(r"[dim]\[git-loco][/dim]")
    status = _try_windows()

    if status == "ENABLED":
        console.print("Location services are enabled. Fetching coordinates...")
        coords = _fetch_windows_coordinates()

        print(coords)
    else:
        _show_location_warning(status)


def _show_location_warning(status):
    MESSAGES = {
        "POLICY_DISABLED": (
            "Location access is disabled by Group Policy. Contact your administrator to request access."
        ),
        "MASTER_DISABLED": (
            "Location access is disabled because location services are OFF.\n"
            "To fix this, go to Settings → Privacy & security → Location and turn ON 'Location services'."
        ),
        "APPS_DISABLED": (
            "Location access is disabled for apps.\n"
            "To fix this, go to Settings → Privacy & security → Location and turn ON 'Let apps access your location'."
        ),
        "DESKTOP_DISABLED": (
            "Location access is disabled for desktop apps.\n"
            "To fix this, go to Settings → Privacy & security → Location and turn ON 'Let desktop apps access your location'."
        ),
    }

    msg = MESSAGES.get(
        status,
        "Could not verify location permissions. Please check Windows Location Settings.",
    )
    
    console.print(f"[red]{msg}[red]")


def _try_windows():
    try:
        script_path = os.path.join("src", "scripts", "location-enabled.ps1")
        ps = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                script_path,
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        return ps.stdout.strip()
    except Exception:
        return "UNKNOWN_ERROR"


def _fetch_windows_coordinates():
    try:
        script_path = os.path.join("src", "scripts", "get-location.ps1")
        ps = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                script_path,
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if ps.stdout.strip():
            return json.loads(ps.stdout.strip())
    except Exception as e:
        return {"error": str(e)}
    return None

def main():
    args = sys.argv[1:]
    result = subprocess.run(["git"] + args, check=False)

    if result.returncode == 0:
        if "commit" in args:
            get_location()
            print("post-commit: done")
        elif "push" in args:
            get_location()
            print("post-push: done")

    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
