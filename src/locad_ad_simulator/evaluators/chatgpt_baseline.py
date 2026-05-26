from __future__ import annotations

from typing import Any

from locad_ad_simulator.ad.claim_extractor import extract_ad_claims


def generic_chatgpt_baseline(ad_copy: str) -> dict[str, Any]:
    info = extract_ad_claims(ad_copy)
    stats = info["stats"]
    findings = []
    if not stats.get("has_cta"):
        findings.append("CTA is vague or missing.")
    if not (stats.get("has_number") or stats.get("has_percentage")):
        findings.append("Ad needs more concrete proof or quantified evidence.")
    if any(t in ad_copy.lower() for t in ["scale", "grow", "seamless", "all-in-one"]):
        findings.append("Some language may feel generic and could apply to many logistics providers.")
    if any(t in ad_copy.lower() for t in ["cost", "margin", "fulfillment"]):
        findings.append("Founder/operator personas may resonate with the cost or fulfillment angle.")
    if not findings:
        findings.append("Ad is reasonably clear, but should still be tested with target segments.")
    return {
        "method": "generic_10_persona_prompt_baseline_simulation",
        "what_generic_chatgpt_would_likely_find": findings,
        "limitations": [
            "No trace to Locad ICP rows or value props.",
            "No measured panel coverage.",
            "No buying-committee objection flow.",
            "No benchmark or gate calibration.",
        ],
    }


def differential_value(baseline: dict[str, Any], evidence_lint: dict[str, Any], coverage: dict[str, Any], committee: dict[str, Any]) -> dict[str, Any]:
    additions = []
    if evidence_lint.get("icp_evidence_refs"):
        additions.append("Traceable ICP evidence: critique maps to specific ICP IDs, pain points, value props, and objections.")
    if coverage.get("coverage_score") is not None:
        additions.append(f"Measured panel coverage: {coverage.get('coverage_score')} across configured ICP axes.")
    if evidence_lint.get("violated_rules"):
        additions.append("Locad-specific rules: catches do/don't and restricted-claim violations.")
    if evidence_lint.get("missing_proof"):
        additions.append("Proof-gap diagnostics: specifies which claims require case studies, SLA data, benchmarks, or integration proof.")
    if committee.get("internal_objections"):
        additions.append("Buying committee simulation: shows which internal stakeholder would block demo intent and why.")
    return {
        "generic_baseline_findings": baseline.get("what_generic_chatgpt_would_likely_find", []),
        "locad_validator_additions": additions,
        "summary": "The Locad validator adds data grounding, traceability, coverage, and decision workflow on top of generic persona reactions.",
    }
