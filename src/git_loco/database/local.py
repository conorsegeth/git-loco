import sqlite3
from dataclasses import asdict
from pathlib import Path

from platformdirs import user_data_dir

from git_loco.database.migrate import migrate
from git_loco.database.store import CommitEntry, Store

APP_NAME = "git-loco"

def _get_db_path() -> Path:
    return Path(user_data_dir(APP_NAME)) / "loco.db"

class LocalStore:
    def __init__(self):
        db_path = _get_db_path()
        db_path.parent.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(db_path, timeout=5) 
        self.conn.execute("PRAGMA journal_mode=WAL")

        migrations_dir = Path(__file__).parent.parent / "migrations"
        migrate(self.conn, migrations_dir)

    def save_commit(self, entry: CommitEntry) -> None:
        query = """
            INSERT INTO commits (
                commit_hash, root_commit_hash, repo_name, repo_path, branch,
                author_name, author_email, message, insertions, deletions,
                files_changed, committed_at, location_status, location_source,
                latitude, longitude, accuracy, offline
            ) VALUES (
                :commit_hash, :root_commit_hash, :repo_name, :repo_path, :branch,
                :author_name, :author_email, :message, :insertions, :deletions,
                :files_changed, :committed_at, :location_status, :location_source,
                :latitude, :longitude, :accuracy, :offline
            )
        """

        with self.conn:
            self.conn.execute(query, asdict(entry))

    def close(self) -> None:
        self.conn.close()