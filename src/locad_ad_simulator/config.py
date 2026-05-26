from __future__ import annotations

from pathlib import Path
from typing import Any
import json

import yaml

from .core.errors import ConfigError


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ConfigError(f"Missing config file: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ConfigError(f"Expected mapping in {path}")
    return data


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def repo_root_from(path: Path | None = None) -> Path:
    current = (path or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "pyproject.toml").exists() and (candidate / "src" / "locad_ad_simulator").exists():
            return candidate
    return current
