from __future__ import annotations

from collections import Counter
from typing import Any

from .dimensions import SCORING_DIMENSIONS, DEFAULT_WEIGHTS
from .confidence import confidence_summary


def aggregate_persona_results(persona_results: list[dict[str, Any]], weights: dict[str, float] | None = None) -> dict[str, Any]:
    weights = weights or DEFAULT_WEIGHTS
    valid = [r for r in persona_results if isinstance(r.get("scores"), dict)]
    if not valid:
        return {"persona_count": 0, "avg_scores": {}, "avg_overall": 0, "verdict_breakdown": {}, "panel_verdict": "NO-GO"}
    avg_scores: dict[str, float] = {}
    for dim in SCORING_DIMENSIONS:
        avg_scores[dim] = round(sum(float(r["scores"].get(dim, 0)) for r in valid) / len(valid), 1)
    weighted = sum(avg_scores.get(dim, 0) * weights.get(dim, 0) for dim in SCORING_DIMENSIONS) / max(sum(weights.values()), 1e-9)
    breakdown = Counter(r.get("verdict", "NO-GO") for r in valid)
    n = len(valid)
    go_rate = breakdown.get("GO", 0) / n
    weak_rate = breakdown.get("WEAK", 0) / n
    no_go_rate = breakdown.get("NO-GO", 0) / n
    panel_verdict = "GO" if go_rate >= 0.55 else "WEAK" if go_rate + weak_rate >= 0.6 else "NO-GO"
    return {
        "persona_count": n,
        "avg_scores": avg_scores,
        "avg_overall": round(weighted, 1),
        "go_rate": round(go_rate, 3),
        "weak_rate": round(weak_rate, 3),
        "no_go_rate": round(no_go_rate, 3),
        "verdict_breakdown": {"GO": breakdown.get("GO", 0), "WEAK": breakdown.get("WEAK", 0), "NO-GO": breakdown.get("NO-GO", 0)},
        "panel_verdict": panel_verdict,
        "confidence": confidence_summary(valid),
    }
