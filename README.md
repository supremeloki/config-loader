# config-loader

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Layered configuration loading: JSON + .env files merged in order, dotted-path access, `${VAR:-default}` environment references, and strictly typed accessors that fail loudly.

## 🚀 Overview

Configuration sprawl — defaults scattered, env vars stringly-typed, typos returning `None` silently. `config-loader` stacks config layers (defaults → base file → override file) with recursive deep-merge, exposes values through dotted paths (`db.port`), resolves `${MY_TOKEN}` references from the environment at read time, and offers `require_int/str/bool` accessors that raise instead of leaking wrong types into your app.

## ✨ Features

- **Formats:** `.json` and `.env` (comments, quoted values); anything else rejected
- **Layered merge:** later layers win; nested dicts merge recursively
- **Dotted paths:** `"app.server.workers"` without manual dict walking
- **Strict missing-key contract:** no default passed → `MissingKeyError`; default passed → returned
- **Env references:** `${VAR}` and `${VAR:-fallback}` resolved recursively through dicts/lists
- **Typed accessors:** `require_int/str/bool` with the Python bool⊂int trap guarded
- **Zero dependencies**

## 🚧 Structure

```
config-loader/
├── src/config_loader/
│   ├── __init__.py
│   └── core.py
├── tests/
│   └── test_core.py
├── README.md
└── pyproject.toml
```

## 📦 Installation

```bash
git clone https://github.com/supremeloki/config-loader.git
cd config-loader
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

## 📋 Requirements

- Python 3.11+
- No runtime dependencies

## 🏃 Quick Start

```python
from pathlib import Path
from config_loader import ConfigLoader

config = (
    ConfigLoader()
    .load_defaults({"app": {"workers": 2}})
    .load_file(Path("config/base.json"))
    .load_file(Path("config/local.json"))
)

workers = config.require_int("app.workers")
token = config.get("api.token")            # ${API_TOKEN} resolved from env
debug = config.get("app.debug", default=False)
```

## 🔧 Error Handling

```text
ConfigError
├── ConfigFileNotFoundError   # layer file absent
├── UnsupportedFormatError    # .yaml/.toml/etc rejected
├── MissingKeyError           # dotted path miss with no default
└── type mismatch             # require_* on the wrong shape
```

## 🧪 Testing

```bash
pytest tests/ -v
```

## 📝 Code Quality

- Full type hints (`X | None` style), frozen source records
- Zero comments — names carry the meaning
- Merge precedence, env resolution, and the strict-missing contract fully covered

## 📄 License

MIT — see [LICENSE](LICENSE).

## 👤 Author

**Kooroush Masoumi** - [kooroushmasoumi@gmail.com](mailto:kooroushmasoumi@gmail.com)

---

⭐ Star this repo if you find it useful!
