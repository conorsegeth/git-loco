import sys
from argparse import ArgumentParser
from sqlite3 import OperationalError

from rich.console import Console

from git_loco.config import (
    APP_NAME,
    ConfigError,
    clear_provider_config,
    config_path,
    load_provider_config,
    save_provider_config,
)
from git_loco.database.providers import PROVIDERS, get_provider
from git_loco.database.store import CommitEntry, get_store
from git_loco.errors import LocationUnavailableError, ProviderError
from git_loco.platforms import windows
from git_loco.types import Coordinates
from git_loco.utils import (
    get_hooks_dir,
    git_metadata,
    is_in_repo,
    is_offline,
    is_windows,
    is_wsl,
)

console = Console()

MARKER = f"Installed by {APP_NAME}"
CAPTURE_CMD = f"{APP_NAME} capture"
DISABLE_CMD = f"{APP_NAME} disable"

HOOK_SCRIPT = f"""#!/bin/sh
# {MARKER}
# To uninstall, delete this file or run: {DISABLE_CMD}
{CAPTURE_CMD}
"""


def get_location() -> Coordinates:
    if not (is_windows() or is_wsl()):
        raise LocationUnavailableError(
            "Location capture only supported on Windows/WSL."
        )

    return windows.get_location()


def install_hooks():
    hooks_dir = get_hooks_dir()
    hooks_dir.mkdir(parents=True, exist_ok=True)


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
            console.print(
                "[yellow]git-loco hook already installed in this repo.[/yellow]"
            )
            return

        console.print(f"A post-commit hook already exists at: {hook_path}")
        console.print(f"To enable commit capture, add this line to it: {CAPTURE_CMD}")
        return

    hook_path.write_text(HOOK_SCRIPT)
    hook_path.chmod(hook_path.stat().st_mode | 0o111)  # make the hook file executable

    console.print("enabled")


def cmd_disable():
    if not is_in_repo():
        console.print("[red]Not inside a git repository.[/red]")
        sys.exit(1)

    hooks_dir = get_hooks_dir()
    hook_path = hooks_dir / "post-commit"

    if not hook_path.exists():
        console.print("disabled")
        return

    hook_text = hook_path.read_text()
    if MARKER not in hook_text:
        console.print(f"To disable commit capture, remove '{CAPTURE_CMD}' from: {hook_path}")
        return

    hook_path.unlink()
    console.print("disabled")


def cmd_capture():
    console.print()
    console.print(r"[dim]\[git-loco] Capturing...[/dim]")

    if not (is_windows() or is_wsl()):
        console.print(r"[red]\[git-loco] Platform not supported.[/red]")
        sys.exit(1)

    meta = git_metadata()
    offline = is_offline()
    location = None

    if not offline:
        try:
            location = get_location()
        except LocationUnavailableError as e:
            console.print(fr"[yellow]\[git-loco] {e}[/yellow]")

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
        console.print(r"[dim]\[git-loco] Captured![/dim]")
    except OperationalError:
        console.print(r"[red]\[git-loco] Failed. Database error.[/red]")
    finally:
        store.close()

    console.print()


def cmd_sync(args):
    if args.provider:
        try:
            provider_cls = get_provider(args.provider)
        except ProviderError as e:
            console.print(f"[red]{e}[/red]")
            sys.exit(1)

        targets = [provider_cls]

    else:
        targets = [cls for cls in PROVIDERS.values() if load_provider_config(cls)]
        if not targets:
            console.print("[yellow]No providers configured.[/yellow]")
            console.print(f"Run '{APP_NAME} config <provider> set' to configure a provider.")
            return

    store = get_store()
    try:
        local = store.fetch_commits()
    except OperationalError as e:
        console.print(f"[red]{e}[/red]")
        sys.exit(1)
    finally:
        store.close()

    console.print(f"Syncing to {len(targets)} provider(s)...")

    failed = False
    for provider_cls in targets:
        name = provider_cls.name
        config = load_provider_config(provider_cls)

        if config is None:
            console.print(f"[yellow]{name}: not configured, skipping...[/yellow]")
            continue

        try:
            provider = provider_cls(config)
            provider.ensure_schema()

            remote_hashes = provider.commit_hashes()

            pending = [entry for entry in local if entry.commit_hash not in remote_hashes]
            if pending:
                provider.insert_commits(pending)

            console.print(f"[green]{name}: synced {len(pending)} commit(s).")
        except ProviderError as e:
            console.print(f"[red]{name}: {e}[/red]")
            failed = True

    if failed:
        sys.exit(1)


def cmd_providers():
    console.print()
    console.print("local: [green]configured[/green]")

    for name, cls in PROVIDERS.items():
        status = (
            "[green]configured[/green]" if load_provider_config(cls) else "[dim]not configured[/dim]"
        )
        console.print(f"[white]{name}[/white]: {status}")

    console.print()


def cmd_config(args):
    try:
        provider_cls = get_provider(args.provider)
    except ProviderError as e:
        console.print(f"[red]{e}[/red]")
        sys.exit(1)

    if args.provider_action == "show":
        path = config_path()
        config = load_provider_config(provider_cls)
        console.print()
        console.print(f"Config file: [white]{path}[/white]")
        if config is None:
            console.print(f"[yellow]{args.provider}: not configured[/yellow]")
        else:
            console.print(f"[green]{args.provider}: configured[/green]")
            for key, value in config.items():
                shown = (
                    f"…{value[-4:]}"
                    if key in ("token", "secret", "password")
                    else value
                )
                console.print(f"  {key}: {shown}")
        console.print()
    elif args.provider_action == "set":
        try:
            values = {key: getattr(args, key) for key in provider_cls.config_keys}
            save_provider_config(provider_cls.name, values)
        except (ConfigError, OSError) as e:
            console.print(f"[red]{e}[/red]")
            console.print(
                f"[yellow]Recovery: delete {config_path()} and rerun this command.[/yellow]"
            )
            sys.exit(1)
        console.print()
        console.print(f"[green]{args.provider} config saved.[/green]")
        console.print()
    elif args.provider_action == "clear":
        try:
            clear_provider_config(provider_cls.name)
        except (ConfigError, OSError) as e:
            console.print(f"[red]{e}[/red]")
            console.print(
                f"[yellow]Recovery: delete {config_path()} and rerun this command.[/yellow]"
            )
            sys.exit(1)
        console.print()
        console.print(f"[green]{args.provider} config cleared.[/green]")
        console.print()


def main() -> None:
    parser = ArgumentParser(
        prog="git-loco", description="Capture commit location and metadata."
    )

    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("enable", help="install the post-commit hook")
    sub.add_parser("disable", help="remove the post-commit hook")
    sub.add_parser("capture", help="capture current location and commit metadata")
    sub.add_parser("providers", help="list available sync providers")

    sync_parser = sub.add_parser("sync", help="sync local commits to a provider")
    sync_parser.add_argument(
        "provider", nargs="?", help="provider name (default: all configured)"
    )

    config_parser = sub.add_parser(
        "config", help="show or update provider configuration"
    )
    config_sub = config_parser.add_subparsers(dest="provider", required=True)
    for name, cls in PROVIDERS.items():
        provider_parser = config_sub.add_parser(
            name, help=f"configure the {name} provider"
        )
        action = provider_parser.add_subparsers(dest="provider_action", required=True)
        action.add_parser("show", help="show current config")
        action.add_parser("clear", help="remove config")
        set_parser = action.add_parser("set", help="save config")
        for key in cls.config_keys:
            set_parser.add_argument(f"--{key.replace('_', '-')}", required=True)

    args = parser.parse_args()

    if args.command == "enable":
        cmd_enable()
    if args.command == "disable":
        cmd_disable()
    if args.command == "capture":
        cmd_capture()
    if args.command == "sync":
        cmd_sync(args)
    if args.command == "providers":
        cmd_providers()
    if args.command == "config":
        cmd_config(args)


if __name__ == "__main__":
    main()
