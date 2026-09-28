import sys
from sqlite3 import OperationalError
from typing import Annotated

import typer

from git_loco.config import APP_NAME, load_provider_config
from git_loco.database.providers import PROVIDERS, get_provider
from git_loco.database.store import get_store
from git_loco.errors import ProviderError


def sync(
    provider: Annotated[
        str | None, typer.Argument(help="provider name (default: all configured)")
    ] = None,
):
    """Sync local commits to a provider."""
    if provider:
        try:
            provider_cls = get_provider(provider)
        except ProviderError as e:
            typer.echo(f"{e}", err=True)
            sys.exit(1)

        targets = [provider_cls]

    else:
        targets = [cls for cls in PROVIDERS.values() if load_provider_config(cls)]
        if not targets:
            typer.echo("No providers configured.")
            typer.echo(f"Run '{APP_NAME} config set <provider>' to configure a provider.")
            return

    store = get_store()
    try:
        local = store.fetch_commits()
    except OperationalError as e:
        typer.echo(f"{e}", err=True)
        sys.exit(1)
    finally:
        store.close()

    typer.echo(f"Syncing to {len(targets)} provider(s)...")

    failed = False
    for provider_cls in targets:
        name = provider_cls.name
        config = load_provider_config(provider_cls)

        if config is None:
            typer.echo(f"{name}: not configured, skipping...")
            continue

        try:
            provider_instance = provider_cls(config)
            provider_instance.ensure_schema()

            remote_hashes = provider_instance.get_commit_hashes()

            pending = [entry for entry in local if entry.commit_hash not in remote_hashes]
            already_present = len(local) - len(pending)

            synced = 0
            if pending:
                synced = provider_instance.insert_commits(pending)

            typer.echo(f"{name}: synced {synced} commit(s), {already_present} already present.")
        except ProviderError as e:
            typer.echo(f"{name}: {e}", err=True)
            failed = True

    if failed:
        sys.exit(1)


def providers():
    """List available sync providers."""
    typer.echo("local (built-in)")

    for name, cls in PROVIDERS.items():
        status = "configured" if load_provider_config(cls) else "not configured"
        typer.echo(f"{name}: {status}")
