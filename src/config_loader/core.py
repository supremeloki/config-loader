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

