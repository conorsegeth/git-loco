import sqlite3
from dataclasses import asdict
from pathlib import Path

from platformdirs import user_data_dir

from git_loco.config import APP_NAME
from git_loco.database.migrations import MIGRATIONS_TABLE_SQL, run_migrations
from git_loco.database.store import COMMIT_COLUMNS, CommitEntry


def _get_db_path() -> Path:
    return Path(user_data_dir(APP_NAME)) / "loco.db"


class LocalStore:
    def __init__(self):
        db_path = _get_db_path()
        db_path.parent.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(db_path, timeout=5)
        self.conn.execute("PRAGMA journal_mode=WAL")

        self._run_migrations()

    # MigrationRunner methdos

    def applied_versions(self) -> set[str]:
        return {
            row[0] for row in self.conn.execute("SELECT version FROM schema_migrations")
        }

    def apply(self, sql: str) -> None:
        self.conn.executescript(sql)

    def mark_applied(self, version: str) -> None:
        self.conn.execute(
            "INSERT INTO schema_migrations (version) VALUES (?)", (version,)
        )

    # Store methods

    def save_commit(self, entry: CommitEntry) -> None:
        cols = ", ".join(COMMIT_COLUMNS)
        placeholders = ", ".join(f":{col}" for col in COMMIT_COLUMNS)
        query = f"INSERT OR IGNORE INTO commits ({cols}) VALUES ({placeholders})"

        with self.conn:
            self.conn.execute(query, asdict(entry))

    def fetch_commits(self) -> list[CommitEntry]:
        rows = self.conn.execute("SELECT * FROM commits").fetchall()
        entries = []

        for row in rows:
            data = dict(zip(COMMIT_COLUMNS, row))
            data["offline"] = bool(data["offline"])

            commit_entry = CommitEntry(**data)
            entries.append(commit_entry)

        return entries

    def close(self) -> None:
        self.conn.close()

    # private methods

    def _run_migrations(self) -> None:
        migrations_dir = Path(__file__).parent / "migrations"

        self.conn.execute(MIGRATIONS_TABLE_SQL)
        run_migrations(list(migrations_dir.glob("*.sql")), self)

        self.conn.commit()
