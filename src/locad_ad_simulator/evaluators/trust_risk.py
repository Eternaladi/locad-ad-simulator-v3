from __future__ import annotations

from typing import Any


def evaluate_trust_risk(evidence_lint: dict[str, Any]) -> dict[str, Any]:
    high = [v for v in evidence_lint.get("violated_rules", []) if v.get("severity") == "high"]
    medium = [v for v in evidence_lint.get("violated_rules", []) if v.get("severity") == "medium"]
    missing = evidence_lint.get("missing_proof", [])
    risk_score = min(10, len(high) * 3 + len(medium) * 1.5 + len(missing) * 1.2)
    if risk_score >= 6:
        level = "high"
    elif risk_score >= 3:
        level = "medium"
    else:
        level = "low"
    return {"risk_level": level, "risk_score": round(risk_score, 1), "high_risk_flags": high, "medium_risk_flags": medium, "missing_proof_count": len(missing)}
