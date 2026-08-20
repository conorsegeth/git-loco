import json
import sys
from pathlib import Path
from typing import Any

from platformdirs import user_config_dir

APP_NAME = "git-loco"


class ConfigError(Exception):
    """Raised when the config file is corrupt."""


def config_path() -> Path:
    return Path(user_config_dir(APP_NAME)) / "config.json"


def _read_config(path: Path) -> dict[str, Any] | None:
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return None
    except (json.JSONDecodeError, OSError) as e:
        raise ConfigError(f"Config file is corrupt or unreadable: {path} ({e})")

    if not isinstance(data, dict):
        raise ConfigError(f"Config file must contain a JSON object: {path}")

    return data


def load_provider_config(provider_cls: type) -> dict[str, str] | None:
    data = _read_config(config_path())

    if data is None:
        return None

    section = data.get(provider_cls.name, {})
    if not isinstance(section, dict):
        raise ConfigError(
            f"config section '{provider_cls.name}' must be an object: {config_path()}"
        )
    
    if any(not section.get(key) for key in provider_cls.config_keys):
        return None

    return {key: section[key] for key in provider_cls.config_keys}


def save_provider_config(name: str, values: dict[str, str]) -> None:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    data = _read_config(path) or {}
    data[name] = values

    path.write_text(json.dumps(data, indent=2) + "\n")
    path.chmod(0o600)  # may contain secrets


def clear_provider_config(name: str) -> None:
    path = config_path()
    data = _read_config(path)

    if data is None:
        return

    data.pop(name, None)

    if data:
        path.write_text(json.dumps(data, indent=2) + "\n")
    else:
        path.unlink()
