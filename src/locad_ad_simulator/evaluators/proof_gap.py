from __future__ import annotations

from typing import Any


def evaluate_proof_gaps(evidence_lint: dict[str, Any], panel: list[dict[str, Any]]) -> dict[str, Any]:
    gaps = list(evidence_lint.get("missing_proof", []))
    objections = evidence_lint.get("matched_objections", [])[:5]
    followup_assets = []
    objection_text = " ".join(objections).lower()
    if "migration" in objection_text or "fba" in objection_text:
        followup_assets.append("FBA migration playbook with integration checklist")
    if "damage" in objection_text or "luxury" in objection_text:
        followup_assets.append("Premium SKU handling / loss-damage policy proof")
    if any("cost" in g.lower() or "margin" in g.lower() for g in gaps):
        followup_assets.append("Same-category cost benchmark or before/after fee comparison")
    if not followup_assets:
        followup_assets.append("Same-category case study with before/after logistics metrics")
    return {"gaps": gaps, "objection_drivers": objections, "recommended_followup_assets": followup_assets}
