import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest

from config_loader import (
    ConfigError,
    ConfigFileNotFoundError,
    ConfigLoader,
    MissingKeyError,
    UnsupportedFormatError,
    deep_merge,
    resolve_env_references,
)


def write_json(path: Path, payload: dict) -> Path:
    import json

    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


@pytest.fixture
def base_file(tmp_path):
    return write_json(tmp_path / "base.json", {
        "app": {"name": "ai-suite", "debug": False, "workers": 4},
        "db": {"host": "localhost", "port": 5432},
    })


def test_deep_merge_nested_dicts():
    merged = deep_merge(
        {"db": {"host": "a", "port": 1}, "x": 1},
        {"db": {"host": "b"}, "y": 2},
    )
    assert merged == {"db": {"host": "b", "port": 1}, "x": 1, "y": 2}


def test_load_json_and_dotted_get(base_file):
    loader = ConfigLoader().load_file(base_file)
    assert loader.get("app.name") == "ai-suite"
    assert loader.get("db.port") == 5432


def test_dotted_missing_key_raises_without_default(base_file):
    loader = ConfigLoader().load_file(base_file)
    with pytest.raises(MissingKeyError):
        loader.get("ghost.key")
    assert loader.get("ghost.key", default="fallback") == "fallback"


def test_layered_files_override(tmp_path, base_file):
    override = write_json(tmp_path / "override.json", {
        "app": {"debug": True},
        "db": {"port": 6543},
    })
    loader = ConfigLoader().load_file(base_file).load_file(override)
    assert loader.get("app.debug") is True
    assert loader.get("app.name") == "ai-suite"
    assert loader.get("db.port") == 6543


def test_defaults_underneath_files(base_file):
    loader = (ConfigLoader()
              .load_defaults({"extra": {"flag": True}})
              .load_file(base_file))
    assert loader.get("extra.flag") is True


def test_missing_file_raises(tmp_path):
    with pytest.raises(ConfigFileNotFoundError):
        ConfigLoader().load_file(tmp_path / "nope.json")


def test_unsupported_format_rejected(tmp_path):
    binary = tmp_path / "config.yaml"
    binary.write_text("key: value", encoding="utf-8")
    with pytest.raises(UnsupportedFormatError):
        ConfigLoader().load_file(binary)
