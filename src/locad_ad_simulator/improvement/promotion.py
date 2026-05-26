from __future__ import annotations

from pathlib import Path
import json
from typing import Any


def record_promotion(changelog_path: Path, decision: dict[str, Any]) -> None:
    changelog_path.parent.mkdir(parents=True, exist_ok=True)
    with changelog_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(decision, ensure_ascii=False) + "\n")
