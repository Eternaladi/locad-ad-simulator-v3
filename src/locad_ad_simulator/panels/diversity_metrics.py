from __future__ import annotations

from collections import Counter
from typing import Any


def entropy(values: list[str]) -> float:
    import math
    if not values:
        return 0.0
    counts = Counter(values)
    n = len(values)
    return round(sum(-(c/n) * math.log(c/n, 2) for c in counts.values()), 4)


def unique_ratio(values: list[str]) -> float:
    return round(len(set(values)) / len(values), 4) if values else 0.0


def panel_diversity(panel: list[dict[str, Any]], axes: list[str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for axis in axes:
        vals: list[str] = []
        for atom in panel:
            v = atom.get(axis)
            if isinstance(v, list):
                vals.extend(str(x) for x in v)
            else:
                vals.append(str(v))
        out[axis] = {"unique": len(set(vals)), "unique_ratio": unique_ratio(vals), "entropy": entropy(vals)}
    return out
