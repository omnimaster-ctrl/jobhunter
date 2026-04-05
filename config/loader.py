import copy
import os
from pathlib import Path
from typing import Any

import yaml

_DEFAULT_CONFIG_PATH = Path(__file__).parent / "default_config.yaml"


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge override into base. Override wins on conflicts."""
    result = copy.deepcopy(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


class Config:
    def __init__(self, user_config_path: str = None) -> None:
        self._user_config_path = Path(
            user_config_path or str(Path.home() / ".jobhunter" / "config.yaml")
        )

        with open(_DEFAULT_CONFIG_PATH, "r") as f:
            self._config = yaml.safe_load(f) or {}

        if self._user_config_path.exists():
            with open(self._user_config_path, "r") as f:
                user_data = yaml.safe_load(f) or {}
            self._config = _deep_merge(self._config, user_data)

    @property
    def data(self) -> dict:
        return copy.deepcopy(self._config)

    def get(self, dotted_key: str, default: Any = None) -> Any:
        keys = dotted_key.split(".")
        node = self._config
        for key in keys:
            if not isinstance(node, dict) or key not in node:
                return default
            node = node[key]
        return node

    def ensure_user_config(self) -> None:
        """Create default user config at the configured path if it does not exist."""
        if not self._user_config_path.exists():
            self._user_config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(_DEFAULT_CONFIG_PATH, "r") as f:
                default_content = f.read()
            with open(self._user_config_path, "w") as f:
                f.write(default_content)
