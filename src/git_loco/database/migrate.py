from pathlib import Path
from sqlite3 import Connection


def migrate(conn: Connection, migrations_dir: Path) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """
    )

    applied = {
        row[0]
        for row in conn.execute("SELECT version FROM schema_migrations")
    }

    for file in sorted(migrations_dir.glob("*.sql")):
        if file.name not in applied:
            conn.executescript(file.read_text())
            conn.execute(
                "INSERT INTO schema_migrations (version) VALUES (?)", 
                (file.name,)
            )
    
    conn.commit()
