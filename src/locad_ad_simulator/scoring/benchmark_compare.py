from __future__ import annotations

from typing import Any


def compare_to_benchmarks(scorecard: dict[str, Any], benchmarks: dict[str, Any]) -> dict[str, Any]:
    history = benchmarks.get("ad_history", [])
    if not history:
        return {"available": False, "summary": "No benchmark history available."}
    out = {"available": True, "positions": {}, "nearest_examples": []}
    metrics = {
        "overall_score": scorecard.get("avg_overall", 0),
        "trust": scorecard.get("avg_scores", {}).get("trust", 0),
        "proof_sufficiency": scorecard.get("avg_scores", {}).get("proof_sufficiency", 0),
        "go_rate": scorecard.get("go_rate", 0),
    }
    for metric, value in metrics.items():
        vals = []
        for row in history:
            try:
                vals.append(float(row.get(metric, 0)))
            except Exception:
                pass
        if vals:
            percentile = sum(1 for v in vals if v <= float(value)) / len(vals)
            out["positions"][metric] = {"value": round(float(value), 3), "percentile_vs_history": round(percentile, 3)}
    # nearest examples by overall score
    def dist(row: dict[str, Any]) -> float:
        try:
            return abs(float(row.get("overall_score", 0)) - float(scorecard.get("avg_overall", 0)))
        except Exception:
            return 99.0
    out["nearest_examples"] = sorted(history, key=dist)[:3]
    return out
