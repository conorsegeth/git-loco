from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class CommitEntry:
    commit_hash: str
    root_commit_hash: str
    repo_name: str
    repo_path: str
    branch: str | None
    author_name: str
    author_email: str
    message: str | None
    insertions: int | None
    deletions: int | None
    files_changed: int
    committed_at: str
    location_status: str
    location_source: str | None
    latitude: float | None
    longitude: float | None
    accuracy: float | None
    offline: bool


COMMIT_COLUMNS = tuple(CommitEntry.__dataclass_fields__)


class Store(Protocol):
    def save_commit(self, entry: CommitEntry) -> None: ...

    def fetch_commits(self) -> list[CommitEntry]: ...

    def close(self) -> None: ...


def get_store() -> Store:
    from git_loco.database.local import LocalStore

    return LocalStore()
