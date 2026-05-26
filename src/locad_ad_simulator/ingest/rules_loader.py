from __future__ import annotations

from pathlib import Path
from typing import Any

from locad_ad_simulator.config import load_yaml


def load_rules(rules_dir: Path) -> dict[str, Any]:
    data: dict[str, Any] = {}
    for path in sorted(rules_dir.glob("*.yaml")):
        data[path.stem] = load_yaml(path)
    return data
