from __future__ import annotations

from statistics import pstdev
from typing import Any


def confidence_summary(persona_results: list[dict[str, Any]]) -> dict[str, Any]:
    scores = [float(r.get("overall_score", 0)) for r in persona_results if r.get("overall_score") is not None]
    if not scores:
        return {"level": "low", "reason": "No valid persona scores"}
    stdev = pstdev(scores) if len(scores) > 1 else 0.0
    agreement = len([s for s in scores if s >= 6.8]) / len(scores)
    if stdev <= 1.0 and agreement >= 0.65:
        level = "high"
    elif stdev <= 1.7:
        level = "medium"
    else:
        level = "low"
    return {"level": level, "overall_stdev": round(stdev, 2), "positive_agreement_rate": round(agreement, 3), "sample_size": len(scores)}
