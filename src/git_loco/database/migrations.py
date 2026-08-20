from pathlib import Path
from typing import Protocol

MIGRATIONS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


class MigrationRunner(Protocol):
    def applied_versions(self) -> set[str]:
        """Migration file names already recorded as applied."""
        ...

    def apply(self, sql: str) -> None:
        """Execute a migration file's SQL."""
        ...

    def mark_applied(self, version: str) -> None:
        """Record a migration file name as applied."""
        ...


def run_migrations(migration_paths: list[Path], runner: MigrationRunner) -> None:
    applied = runner.applied_versions()
    for migration_path in sorted(migration_paths):
        if migration_path.name not in applied:
            runner.apply(migration_path.read_text())
            runner.mark_applied(migration_path.name)
