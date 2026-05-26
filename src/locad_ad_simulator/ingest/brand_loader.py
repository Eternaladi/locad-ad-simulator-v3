from __future__ import annotations

from pathlib import Path
from typing import Any

from locad_ad_simulator.config import load_yaml


def load_brand_context(brand_dir: Path) -> dict[str, Any]:
    context: dict[str, Any] = {}
    for name in ["locad", "positioning", "proof_points", "competitors", "restricted_claims"]:
        path = brand_dir / f"{name}.yaml"
        if path.exists():
            context[name] = load_yaml(path)
    return context
