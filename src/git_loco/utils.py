import platform


def is_windows() -> bool:
    return platform.system() == "Windows"


def is_wsl() -> bool:
    return "microsoft" in platform.uname().release.lower()
