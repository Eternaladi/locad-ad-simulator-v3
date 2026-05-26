from __future__ import annotations

from collections import Counter
from typing import Any

from locad_ad_simulator.ad.claim_extractor import extract_ad_claims
from .base import overlap_score


def lint_ad_evidence(ad_copy: str, panel: list[dict[str, Any]], brand: dict[str, Any], rules: dict[str, Any]) -> dict[str, Any]:
    claim_info = extract_ad_claims(ad_copy)
    pain_candidates = list(dict.fromkeys(p for atom in panel for p in atom.get("top_pain_points", [])))
    value_candidates = list(dict.fromkeys(v for atom in panel for v in atom.get("locad_value_propositions", []) + atom.get("key_motivations", [])))
    objection_candidates = list(dict.fromkeys(o for atom in panel for o in atom.get("likely_objections", [])))
    _, matched_pains = overlap_score(ad_copy, pain_candidates)
    _, matched_values = overlap_score(ad_copy, value_candidates)
    _, matched_objections = overlap_score(ad_copy, objection_candidates)

    violations = _check_rules(ad_copy, claim_info, rules)
    restricted = _check_restricted_claims(ad_copy, brand)
    missing_proof = _missing_proof(ad_copy, claim_info, matched_objections)
    proof_points = _matched_brand_proof(ad_copy, brand)
    icp_refs = _icp_references(panel, matched_pains, matched_values, matched_objections)
    summary = _summary(matched_pains, matched_values, missing_proof, violations, restricted)
    return {
        "summary": summary,
        "ad_claims": claim_info,
        "matched_pain_points": matched_pains,
        "matched_value_props": matched_values,
        "matched_objections": matched_objections,
        "matched_brand_proof_points": proof_points,
        "missing_proof": missing_proof,
        "violated_rules": violations + restricted,
        "icp_evidence_refs": icp_refs,
        "recommended_rewrite": _recommended_rewrite(matched_pains, matched_values, missing_proof),
    }


def _check_rules(ad_copy: str, claim_info: dict[str, Any], rules: dict[str, Any]) -> list[dict[str, Any]]:
    lower = ad_copy.lower()
    out: list[dict[str, Any]] = []
    for rule in rules.get("dos_and_donts", {}).get("rules", []):
        for pattern in rule.get("bad_patterns", []) or []:
            if pattern.lower() in lower:
                out.append({"id": rule["id"], "severity": rule.get("severity", "medium"), "reason": rule.get("description"), "evidence": pattern})
        applies = [t for t in rule.get("applies_when_claim_mentions", []) or [] if t.lower() in lower]
        if applies:
            required = rule.get("required_evidence", []) or []
            if not _has_required_evidence(claim_info, required, lower):
                out.append({"id": rule["id"], "severity": rule.get("severity", "medium"), "reason": rule.get("description"), "evidence": f"mentions {', '.join(applies)} but lacks {', '.join(required)}"})
    for risk in rules.get("risk_rules", {}).get("risk_patterns", []):
        for pattern in risk.get("patterns", []) or []:
            if pattern.lower() in lower:
                out.append({"id": risk["id"], "severity": risk.get("severity", "medium"), "reason": risk.get("description", "Risky language pattern"), "evidence": pattern})
    return out


def _has_required_evidence(claim_info: dict[str, Any], required: list[str], lower: str) -> bool:
    signals = claim_info.get("proof_signals", {})
    if not required:
        return True
    for req in required:
        r = req.lower()
        if r == "percentage" and signals.get("percentage"):
            return True
        if r in ["case study", "benchmark", "before/after", "fee comparison"] and (signals.get("case_study") or signals.get("benchmark")):
            return True
        if r in ["sla", "region", "carrier", "warehouse coverage"] and (signals.get("sla") or signals.get("number") or signals.get("integration")):
            return True
        if r in lower:
            return True
    return False


def _check_restricted_claims(ad_copy: str, brand: dict[str, Any]) -> list[dict[str, Any]]:
    lower = ad_copy.lower()
    out: list[dict[str, Any]] = []
    for rc in brand.get("restricted_claims", {}).get("restricted_claims", []):
        for phrase in rc.get("phrases", []):
            if phrase.lower() in lower:
                out.append({"id": rc.get("id"), "severity": rc.get("severity", "high"), "reason": rc.get("reason"), "evidence": phrase})
    return out


def _matched_brand_proof(ad_copy: str, brand: dict[str, Any]) -> list[dict[str, Any]]:
    lower = ad_copy.lower()
    out = []
    for pp in brand.get("proof_points", {}).get("proof_points", []):
        claim = pp.get("claim", "")
        words = [w for w in claim.lower().replace("/", " ").split() if len(w) > 3]
        if sum(1 for w in words if w in lower) >= max(1, min(3, len(words)//3)):
            out.append(pp)
    return out


def _missing_proof(ad_copy: str, claim_info: dict[str, Any], matched_objections: list[str]) -> list[str]:
    missing: list[str] = []
    cats = set(claim_info.get("categories", []))
    signals = claim_info.get("proof_signals", {})
    if "cost" in cats and not (signals.get("percentage") or signals.get("benchmark") or signals.get("case_study")):
        missing.append("Cost/margin claim needs a percentage, benchmark, or same-category case study.")
    if "speed" in cats and not (signals.get("percentage") or signals.get("sla") or signals.get("time_bound")):
        missing.append("Speed/SLA claim needs region-specific SLA or fulfillment-rate evidence.")
    if "inventory" in cats and not signals.get("integration"):
        missing.append("Inventory claim needs integration or sync-frequency proof.")
    if "cross_border" in cats and not any(t in ad_copy.lower() for t in ["uae", "ksa", "gcc", "compliance", "customs", "noon", "salla", "zid"]):
        missing.append("Cross-border claim needs region, compliance, or marketplace detail.")
    objections_lower = " ".join(matched_objections).lower()
    if "migration" in objections_lower or "fba" in objections_lower:
        missing.append("Migration/FBA anxiety needs onboarding, integration, or switching proof.")
    if "damage" in objections_lower or "luxury" in objections_lower:
        missing.append("Premium SKU concern needs loss/damage handling or white-glove fulfillment proof.")
    return list(dict.fromkeys(missing))


def _icp_references(panel: list[dict[str, Any]], pains: list[str], values: list[str], objections: list[str]) -> list[dict[str, Any]]:
    refs = []
    for atom in panel:
        evidence = []
        for field, matches in [("top_pain_points", pains), ("locad_value_propositions", values), ("likely_objections", objections)]:
            for item in atom.get(field, []):
                if item in matches:
                    evidence.append({"field": field, "text": item})
        if evidence:
            refs.append({"icp_id": atom.get("icp_id"), "persona": atom.get("persona"), "region": atom.get("region"), "evidence": evidence[:4]})
    return refs[:12]


def _summary(pains: list[str], values: list[str], missing: list[str], violations: list[dict[str, Any]], restricted: list[dict[str, Any]]) -> str:
    if restricted:
        return "High-risk creative: contains restricted/overclaiming language that should be revised before launch."
    if pains and values and not missing and not violations:
        return "Strong evidence alignment: the ad maps to ICP pain points and Locad value props with acceptable proof."
    if pains and values:
        return "Directionally strong but needs proof/rule cleanup before it becomes decision-grade."
    if pains or values:
        return "Partial ICP fit: the ad catches one side of the pain/value pair but needs sharper Locad-specific evidence."
    return "Weak ICP fit: the ad currently reads like generic logistics copy rather than Locad-specific validation."


def _recommended_rewrite(pains: list[str], values: list[str], missing: list[str]) -> str:
    pain = pains[0] if pains else "fulfillment costs and marketplace SLA risk"
    value = values[0] if values else "inventory sync, multi-carrier fulfillment, and peak-season controls"
    proof = " Add a same-category proof point." if missing else ""
    return f"Lead with '{pain}', connect it to '{value}', and use a concrete CTA like 'Book a 15-minute fulfillment fit check'.{proof}"
