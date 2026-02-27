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

