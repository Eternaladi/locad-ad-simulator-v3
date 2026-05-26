from __future__ import annotations

from collections import Counter
from typing import Any


def axis_values(atoms: list[dict[str, Any]], axis: str) -> set[str]:
    vals: set[str] = set()
    for atom in atoms:
        value = atom.get(axis)
        if isinstance(value, list):
            vals.update(str(v) for v in value if str(v).strip())
        elif value is not None:
            vals.add(str(value))
    return vals


def coverage_report(panel: list[dict[str, Any]], universe: list[dict[str, Any]], required_axes: list[str]) -> dict[str, Any]:
    axis_reports: dict[str, Any] = {}
    ratios = []
    for axis in required_axes:
        universe_vals = axis_values(universe, axis)
        panel_vals = axis_values(panel, axis)
        ratio = len(panel_vals & universe_vals) / len(universe_vals) if universe_vals else 1.0
        ratios.append(ratio)
        axis_reports[axis] = {
            "covered": sorted(panel_vals & universe_vals),
            "missing_count": max(len(universe_vals - panel_vals), 0),
            "universe_count": len(universe_vals),
            "coverage_ratio": round(ratio, 3),
        }
    missing_segments = summarize_missing_segments(panel, universe)
    return {
        "panel_size": len(panel),
        "coverage_score": round(sum(ratios) / len(ratios), 3) if ratios else 1.0,
        "axes": axis_reports,
        "missing_segments": missing_segments,
    }


def summarize_missing_segments(panel: list[dict[str, Any]], universe: list[dict[str, Any]], limit: int = 8) -> list[str]:
    panel_combos = {f"{a.get('region')} / {a.get('persona')} / {a.get('primary_marketplace')}" for a in panel}
    counter: Counter[str] = Counter()
    for atom in universe:
        combo = f"{atom.get('region')} / {atom.get('persona')} / {atom.get('primary_marketplace')}"
        if combo not in panel_combos:
            counter[combo] += 1
    return [f"{combo} ({count} ICPs)" for combo, count in counter.most_common(limit)]
