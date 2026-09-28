from typing import ClassVar, Protocol

from git_loco.database.store import CommitEntry


class SyncProvider(Protocol):
    name: ClassVar[str]
    config_keys: ClassVar[tuple[str, ...]]

    def __init__(self, config: dict[str, str]) -> None: ...

    def ensure_schema(self) -> None: ...
    def get_commit_hashes(self) -> set[str]: ...
    def insert_commits(self, entries: list[CommitEntry]) -> int: ...
