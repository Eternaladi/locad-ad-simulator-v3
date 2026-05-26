from __future__ import annotations

from pathlib import Path
from typing import Any
import json


def write_json_report(report: dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    return path
