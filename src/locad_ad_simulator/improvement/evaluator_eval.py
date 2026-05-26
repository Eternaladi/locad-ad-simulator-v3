from __future__ import annotations

from typing import Any


def summarize_evaluator_health(reports: list[dict[str, Any]]) -> dict[str, Any]:
    if not reports:
        return {"status": "no_reports"}
    verdicts = [r.get("gate_decision", {}).get("verdict") for r in reports]
    return {"runs": len(reports), "verdict_counts": {v: verdicts.count(v) for v in sorted(set(verdicts))}}
