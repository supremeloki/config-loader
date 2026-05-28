from __future__ import annotations

import json
import os
import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ConfigError(Exception):
    pass


class ConfigFileNotFoundError(ConfigError):
    def __init__(self, path: Path) -> None:
        super().__init__(f"config file not found: {path}")


class UnsupportedFormatError(ConfigError):
    def __init__(self, suffix: str) -> None:
        super().__init__(f"unsupported config format: {suffix!r}")


class MissingKeyError(ConfigError):
    def __init__(self, key: str) -> None:
        super().__init__(f"required config key missing: {key!r}")


class TypeError_(ConfigError):
    def __init__(self, key: str, expected: type, actual: type) -> None:
        super().__init__(
            f"key {key!r} expected {expected.__name__}, got {actual.__name__}"
        )


ENV_REF_PATTERN: re.Pattern[str] = re.compile(r"^\$\{([A-Z0-9_]+)(?::-(.*))?\}$")

_UNSET = object()


@dataclass(frozen=True)
class ConfigSource:
    path: Path
    layer_name: str


def parse_json(text: str) -> dict[str, Any]:
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ConfigError("top-level JSON must be an object")
    return payload


def parse_env(text: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ConfigError(f"invalid env line {line_number}: {raw_line!r}")
        key, _, value = line.partition("=")
        result[key.strip()] = value.strip().strip('"').strip("'")
    return result


PARSERS: dict[str, Callable[[str], dict[str, Any]]] = {
    ".json": parse_json,
    ".env": parse_env,
}


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if (key in merged and isinstance(merged[key], dict)
                and isinstance(value, dict)):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def resolve_env_references(value: Any,
                           environ: dict[str, str] | None = None) -> Any:
    source = environ if environ is not None else dict(os.environ)
    if isinstance(value, str):
        match = ENV_REF_PATTERN.match(value)
        if match:
            name, default = match.group(1), match.group(2)
            return source.get(name, default if default is not None else value)
        return value
    if isinstance(value, dict):
        return {k: resolve_env_references(v, source) for k, v in value.items()}
    if isinstance(value, list):
        return [resolve_env_references(item, source) for item in value]
    return value


class ConfigLoader:
    def __init__(self, *, use_env_refs: bool = True,
                 environ: dict[str, str] | None = None) -> None:
        self._use_env_refs = use_env_refs
        self._environ = environ
        self._layers: list[ConfigSource] = []
        self._merged: dict[str, Any] | None = None

    def load_file(self, path: Path, layer_name: str | None = None) -> "ConfigLoader":
        if not path.exists():
            raise ConfigFileNotFoundError(path)
        parser = PARSERS.get(path.suffix.lower())
        if parser is None:
            raise UnsupportedFormatError(path.suffix)
        data = parser(path.read_text(encoding="utf-8"))
        self._layers.append(ConfigSource(
            path=path, layer_name=layer_name or path.stem,
        ))
        self._merged = data if self._merged is None \
            else deep_merge(self._merged, data)
        return self

    def load_defaults(self, defaults: dict[str, Any]) -> "ConfigLoader":
        self._merged = defaults if self._merged is None \
            else deep_merge(defaults, self._merged)
        return self

    @property
    def data(self) -> dict[str, Any]:
        if self._merged is None:
            return {}
        if self._use_env_refs:
            return resolve_env_references(self._merged, self._environ)
        return dict(self._merged)

    def get(self, key: str, default: Any = _UNSET,
            expected_type: type | tuple[type, ...] | None = None) -> Any:
        current: Any = self.data
        for part in key.split("."):
            if not isinstance(current, dict) or part not in current:
                if default is _UNSET:
                    raise MissingKeyError(key)
                return default
            current = current[part]
        if expected_type is not None and not isinstance(current, expected_type):
            raise TypeError_(key, expected_type if isinstance(expected_type, type)
                             else expected_type[0], type(current))
        return current

    def require_int(self, key: str) -> int:
        value = self.get(key, expected_type=int)
        if isinstance(value, bool):
            raise TypeError_(key, int, bool)
        return int(value)

    def require_str(self, key: str) -> str:
        return str(self.get(key, expected_type=str))

    def require_bool(self, key: str) -> bool:
        value = self.get(key, expected_type=bool)
        if not isinstance(value, bool):
            raise TypeError_(key, bool, type(value))
        return value
