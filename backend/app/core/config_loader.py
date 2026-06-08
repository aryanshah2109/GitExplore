"""Load YAML config and expose it through a small attribute-style wrapper."""

import yaml
from backend.app.core.path_constants import CONFIG_PATH


class Config:
    """Wrap a nested dict so config values can be read with dotted access."""

    def __init__(self, data: dict):
        self._data = data

    def __getattr__(self, key: str):
        """Return a nested config value or raise when the key is missing."""
        if key.startswith("_"):
            raise AttributeError(key)

        if key not in self._data:
            raise AttributeError(f"Config key '{key}' not found")

        value = self._data[key]
        if isinstance(value, dict):
            return Config(value)
        return value

    def get(self, key: str, default=None):
        """Safe access with a fallback default value."""
        value = self._data.get(key, default)
        if isinstance(value, dict):
            return Config(value)
        return value

    def items(self):
        return self._data.items()

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def __iter__(self):
        return iter(self._data)

    def __getitem__(self, key):
        value = self._data[key]
        if isinstance(value, dict):
            return Config(value)
        return value

    def to_dict(self):
        return self._data

    def __repr__(self):
        return f"Config({list(self._data.keys())})"


def load_config() -> dict:
    """Load `config.yaml` and return the parsed mapping."""
    try:
        with open(CONFIG_PATH, "r") as f:
            data = yaml.safe_load(f)

        if not isinstance(data, dict):
            raise ValueError("config.yaml must be a YAML mapping at the top level")

        return data

    except FileNotFoundError:
        raise FileNotFoundError(f"Config file not found at {CONFIG_PATH}")
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing config.yaml: {e}")


config = Config(load_config())
