from __future__ import annotations

from typing import Any

from locad_ad_simulator.simulation.objection_flow import role_objections
from locad_ad_simulator.simulation.journey_outcome import decide_journey
from locad_ad_simulator.simulation.interaction_graph import committee_interaction_graph


def simulate_buying_committee(ad_copy: str, panel: list[dict[str, Any]], evidence_lint: dict[str, Any], scorecard: dict[str, Any] | None = None) -> dict[str, Any]:
    objections = role_objections(ad_copy, evidence_lint)
    outcome = decide_journey(objections, scorecard)
    proof_assets = _best_followup_assets(evidence_lint)
    return {
        **outcome,
        "internal_objections": objections,
        "proof_needed": evidence_lint.get("missing_proof", []),
        "best_followup_assets": proof_assets,
        "interaction_graph": committee_interaction_graph(objections),
    }


def _best_followup_assets(evidence_lint: dict[str, Any]) -> list[str]:
    assets = []
    missing = " ".join(evidence_lint.get("missing_proof", [])).lower()
    if "cost" in missing or "margin" in missing:
        assets.append("Same-category fulfillment cost benchmark with before/after margins")
    if "speed" in missing or "sla" in missing:
        assets.append("Region-specific SLA dashboard screenshot or fulfillment-rate proof")
    if "inventory" in missing or "integration" in missing:
        assets.append("Marketplace integration map and inventory sync demo")
    if "migration" in missing or "fba" in missing:
        assets.append("FBA/3PL migration checklist and customer switching case study")
    if not assets:
        assets.append("Same-category case study with hard logistics metrics")
    return assets
