from __future__ import annotations

from pathlib import Path
from typing import Any

from locad_ad_simulator.config import load_yaml
from .coverage import coverage_report
from .sampling import max_coverage_sample
from .diversity_metrics import panel_diversity


def _matches_filters(atom: dict[str, Any], filters: dict[str, Any]) -> bool:
    for key, expected in filters.items():
        actual = atom.get(key)
        if isinstance(expected, list):
            if actual not in expected:
                return False
        else:
            if actual != expected:
                return False
    return True


def build_panel(atoms: list[dict[str, Any]], panel_config_path: Path, override_size: int | None = None) -> dict[str, Any]:
    config = load_yaml(panel_config_path)
    filters = config.get("filters", {}) or {}
    universe = [a for a in atoms if _matches_filters(a, filters)]
    if not universe:
        raise ValueError(f"Panel config {panel_config_path} matched no ICP atoms")
    size = int(override_size or config.get("size", min(20, len(universe))))
    axes = config.get("required_axes", ["region", "persona", "product_category", "primary_marketplace", "revenue_stage"])
    sampling = config.get("sampling", {}) or {}
    strategy = sampling.get("strategy", "max_coverage")
    seed = int(sampling.get("seed", 42))
    targets = config.get("coverage_targets", {}) or {}
    if strategy != "max_coverage":
        raise ValueError(f"Unsupported sampling strategy: {strategy}")
    panel = max_coverage_sample(universe, size=size, axes=axes, seed=seed, targets=targets)
    coverage = coverage_report(panel, universe, axes)
    coverage["diversity"] = panel_diversity(panel, ["region", "persona", "product_category", "primary_marketplace", "revenue_stage"])
    coverage["panel_name"] = config.get("name", panel_config_path.stem)
    coverage["filters"] = filters
    coverage["required_axes"] = axes
    return {"config": config, "panel": panel, "universe": universe, "coverage": coverage}
