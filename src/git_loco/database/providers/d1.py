import json
import urllib.error
import urllib.request
from dataclasses import astuple
from pathlib import Path

from typing import ClassVar

from git_loco.database.migrations import MIGRATIONS_TABLE_SQL, run_migrations
from git_loco.database.store import COMMIT_COLUMNS, CommitEntry
from git_loco.errors import ProviderError

API_URL = "https://api.cloudflare.com/client/v4/accounts/{account_id}/d1/database/{database_id}/query"
CHUNK_SIZE = 50
MIGRATIONS_DIR = Path(__file__).parent.parent / "migrations"


def _entry_params(entry: CommitEntry) -> list[object]:
    return list(astuple(entry))


class D1Provider:
    name: ClassVar[str] = "d1"
    config_keys: ClassVar[tuple[str, ...]] = ("token", "account_id", "database_id")

    def __init__(self, config: dict[str, str]) -> None:
        self._token = config["token"]
        self._account_id = config["account_id"]
        self._database_id = config["database_id"]

    # MigrationRunner methods

    def applied_versions(self) -> set[str]:
        result = self._query("SELECT version FROM schema_migrations")
        return {row["version"] for row in result[0]["results"]}

    def apply(self, sql: str) -> None:
        self._query(sql)

    def mark_applied(self, version: str) -> None:
        self._query("INSERT INTO schema_migrations (version) VALUES (?)", [version])

    # SyncProvider methods

    def ensure_schema(self) -> None:
        self._query(MIGRATIONS_TABLE_SQL)
        run_migrations(list(MIGRATIONS_DIR.glob("*.sql")), self)

    def get_commit_hashes(self) -> set[str]:
        result = self._query("SELECT commit_hash FROM commits")
        return {row["commit_hash"] for row in result[0]["results"]}

    def insert_commits(self, entries: list[CommitEntry]) -> None:
        cols = ", ".join(COMMIT_COLUMNS)
        placeholders = ", ".join("?" for _ in COMMIT_COLUMNS)
        sql = f"INSERT OR IGNORE INTO commits ({cols}) VALUES ({placeholders})"

        for start in range(0, len(entries), CHUNK_SIZE):
            statements = [
                {"sql": sql, "params": _entry_params(entry)}
                for entry in entries[start : start + CHUNK_SIZE]
            ]

            self._post({"statements": statements})

    # D1 HTTP API methods

    def _query(self, sql: str, params: list | None = None) -> list:
        return self._post({"sql": sql, "params": params or []})

    def _post(self, body: dict) -> list:
        url = API_URL.format(account_id=self._account_id, database_id=self._database_id)
        request = urllib.request.Request(
            url,
            data=json.dumps(body).encode(),
            headers={
                "Authorization": f"Bearer {self._token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.loads(response.read())
        except urllib.error.HTTPError as e:
            raise ProviderError(
                f"D1 API error {e.code}: {e.read().decode('utf-8', 'replace')}"
            )
        except urllib.error.URLError as e:
            raise ProviderError(f"D1 API unreachable: {e.reason}") from e

        if not payload.get("success"):
            raise ProviderError(f"D1 API error: {payload.get('errors')}")

        result = payload["result"]

        failed_statements = [item for item in result if not item.get("success")]
        if failed_statements:
            raise ProviderError(f"D1 statement failed: {failed_statements[0]}")

        return result

