from __future__ import annotations

import random
from collections import Counter
from typing import Any


def _value_set(atom: dict[str, Any], axes: list[str]) -> set[tuple[str, str]]:
    out: set[tuple[str, str]] = set()
    for axis in axes:
        v = atom.get(axis)
        if isinstance(v, list):
            for x in v:
                out.add((axis, str(x)))
        elif v is not None:
            out.add((axis, str(v)))
    return out


def max_coverage_sample(atoms: list[dict[str, Any]], size: int, axes: list[str], seed: int = 42, targets: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    if size >= len(atoms):
        return list(atoms)
    rng = random.Random(seed)
    candidates = list(atoms)
    rng.shuffle(candidates)
    selected: list[dict[str, Any]] = []
    covered: set[tuple[str, str]] = set()
    targets = targets or {}

    while candidates and len(selected) < size:
        best_idx = 0
        best_score = -1.0
        counts = {
            "regions": Counter(a.get("region") for a in selected),
            "personas": Counter(a.get("persona") for a in selected),
        }
        for idx, atom in enumerate(candidates):
            novelty = len(_value_set(atom, axes) - covered)
            target_bonus = 0.0
            if "regions" in targets and atom.get("region") in targets["regions"]:
                desired = targets["regions"][atom.get("region")] * size
                target_bonus += max(desired - counts["regions"][atom.get("region")], 0) * 0.4
            if "personas" in targets and atom.get("persona") in targets["personas"]:
                desired = targets["personas"][atom.get("persona")] * size
                target_bonus += max(desired - counts["personas"][atom.get("persona")], 0) * 0.3
            score = novelty + target_bonus
            if score > best_score:
                best_idx, best_score = idx, score
        chosen = candidates.pop(best_idx)
        selected.append(chosen)
        covered |= _value_set(chosen, axes)
    return selected
