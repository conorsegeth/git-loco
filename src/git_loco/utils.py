import platform
import socket
import subprocess
from pathlib import Path


def is_windows() -> bool:
    return platform.system() == "Windows"


def is_wsl() -> bool:
    return "microsoft" in platform.uname().release.lower()


def is_offline() -> bool:
    try:
        socket.create_connection(("1.1.1.1", 443), timeout=2).close()
        return False
    except OSError:
        return True


def get_hooks_dir() -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--git-path", "hooks"],
        capture_output=True,
        text=True,
        check=True,
    )
    return Path(result.stdout.strip())


def is_in_repo():
    result = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0 and result.stdout.strip() == "true"


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], capture_output=True, text=True, check=False
    )
    return result.stdout.strip()


def git_metadata() -> dict:
    repo_path = _git("rev-parse", "--show-toplevel")
 
    # pull commit hash, author, message, and date in a single call
    # using a delimiter that won't collide with commit content.
    sep = "\x1f"
    commit_hash, author_name, author_email, message, committed_at = _git(
        "log", "-1", f"--format=%H{sep}%an{sep}%ae{sep}%s{sep}%cI"
    ).split(sep)
 
    root_commit_lines = _git("rev-list", "--max-parents=0", "HEAD").splitlines()
    root_commit_hash = root_commit_lines[0] if root_commit_lines else ""
 
    insertions = deletions = files_changed = 0

    numstat = _git("show", "--numstat", "--format=", "HEAD")
    for line in numstat.splitlines():
        added, deleted, _path = line.split("\t", 2)

        if added != "-" and deleted != "-":  # binary files report "-"
            insertions += int(added)
            deletions += int(deleted)

        files_changed += 1

    repo_name = Path(repo_path).name
    branch = _git("branch", "--show-current") or None
    message = message or None
 
    return {
        "commit_hash": commit_hash,
        "root_commit_hash": root_commit_hash,
        "repo_name": repo_name,
        "repo_path": repo_path,
        "branch": branch,
        "author_name": author_name,
        "author_email": author_email,
        "message": message,
        "insertions": insertions,
        "deletions": deletions,
        "files_changed": files_changed,
        "committed_at": committed_at,
    }
