from __future__ import annotations

from typing import Any

from locad_ad_simulator.ad.claim_extractor import extract_ad_claims
from .base import overlap_score, clamp_score


def evaluate_persona_reactions(ad_copy: str, panel: list[dict[str, Any]], evidence: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    claim_info = extract_ad_claims(ad_copy)
    proof_signals = claim_info["proof_signals"]
    has_proof = any(proof_signals.values())
    has_cta = bool(claim_info.get("cta"))
    results: list[dict[str, Any]] = []
    for atom in panel:
        pain_score, matched_pains = overlap_score(ad_copy, atom.get("top_pain_points", []))
        value_score, matched_values = overlap_score(ad_copy, atom.get("locad_value_propositions", []) + atom.get("key_motivations", []))
        objection_score, matched_objections = overlap_score(ad_copy, atom.get("likely_objections", []))
        channel_score, matched_channels = overlap_score(ad_copy, atom.get("sales_channels", []) + [atom.get("primary_marketplace", "")])
        region_score = 1.0 if str(atom.get("region", "")).lower() in ad_copy.lower() else 0.0
        localized_terms = channel_score + region_score

        proof_point_bonus = 0.8 if evidence and evidence.get("matched_brand_proof_points") else 0.0
        relevance = clamp_score(4.0 + pain_score * 3.2 + value_score * 2.3 + min(channel_score, 1) * 1.7 + region_score * 0.9)
        pain_resonance = clamp_score(3.7 + pain_score * 5.8 + (0.8 if matched_pains else 0))
        value_alignment = clamp_score(4.0 + value_score * 5.2 + min(channel_score, 1) * 1.0)
        trust = clamp_score(4.7 + (1.7 if has_proof else 0) + proof_point_bonus + value_score * 2.0 - max(0.0, 0.6 - pain_score) * 0.5)
        clarity = clamp_score(7.5 if len(ad_copy.split()) <= 70 else 6.2)
        if any(word in ad_copy.lower() for word in ["seamless", "all-in-one", "grow faster", "scale your logistics"]):
            clarity = clamp_score(clarity - 1.0)
        cta_pull = clamp_score(4.8 + (1.9 if has_cta else -0.6) + pain_score * 1.6 + (0.7 if "15" in ad_copy else 0))
        localization_fit = clamp_score(4.8 + min(localized_terms, 2.0) * 2.0 + (0.9 if atom.get("region") == "GCC" and any(t in ad_copy.lower() for t in ["ramadan", "noon", "salla", "gcc"]) else 0))
        proof_sufficiency = clamp_score(4.0 + (2.0 if has_proof else 0) + (0.9 if proof_signals.get("percentage") else 0) + (0.7 if proof_signals.get("integration") else 0))

        scores = {
            "relevance": relevance,
            "pain_resonance": pain_resonance,
            "value_prop_alignment": value_alignment,
            "trust": trust,
            "clarity": clarity,
            "cta_pull": cta_pull,
            "localization_fit": localization_fit,
            "proof_sufficiency": proof_sufficiency,
        }
        overall = round(sum(scores.values()) / len(scores), 1)
        if overall >= 6.8 and trust >= 5.8 and proof_sufficiency >= 6.0:
            verdict = "GO"
        elif overall >= 5.6:
            verdict = "WEAK"
        else:
            verdict = "NO-GO"
        first_reaction = _first_reaction(atom, matched_pains, matched_values, matched_objections, verdict)
        results.append({
            "icp_id": atom.get("icp_id"),
            "persona": atom.get("persona"),
            "region": atom.get("region"),
            "decision_maker_title": atom.get("decision_maker_title"),
            "product_category": atom.get("product_category"),
            "primary_marketplace": atom.get("primary_marketplace"),
            "first_reaction": first_reaction,
            "scores": scores,
            "overall_score": overall,
            "would_stop_scrolling": overall >= 6.5,
            "would_click": overall >= 6.8 and has_cta,
            "what_resonated": matched_pains[:2] or matched_values[:2] or ["The ad has a clear logistics angle but did not strongly map to this ICP's exact pain."],
            "what_missed": matched_objections[:2] or _default_misses(atom, proof_sufficiency, localization_fit),
            "matched_pain_points": matched_pains,
            "matched_value_props": matched_values,
            "matched_channels": matched_channels,
            "likely_objections": atom.get("likely_objections", [])[:3],
            "copy_suggestion": _copy_suggestion(atom, matched_pains, matched_values),
            "verdict": verdict,
        })
    return results


def _first_reaction(atom: dict[str, Any], pains: list[str], values: list[str], objections: list[str], verdict: str) -> str:
    if verdict == "GO" and pains:
        return f"This speaks to my world because it names {pains[0].lower()}. I would look for proof that Locad can deliver this in my channel mix."
    if verdict == "WEAK":
        return f"The direction is relevant for a {atom.get('persona')}, but I need sharper proof and less generic logistics language before I would trust it."
    return f"This feels too generic for my operating reality; it does not yet answer the objection: {objections[0] if objections else 'why switch now?'}"


def _default_misses(atom: dict[str, Any], proof: float, localization: float) -> list[str]:
    misses = []
    if proof < 6:
        misses.append("Needs harder proof: case study, SLA number, fee comparison, or integration evidence.")
    if localization < 6:
        misses.append(f"Needs more {atom.get('region')} / {atom.get('primary_marketplace')} context.")
    return misses or ["Could use a more specific buyer trigger and follow-up asset."]


def _copy_suggestion(atom: dict[str, Any], pains: list[str], values: list[str]) -> str:
    pain = pains[0] if pains else (atom.get("top_pain_points", ["ops firefighting"])[0])
    value = values[0] if values else (atom.get("locad_value_propositions", ["multi-channel fulfillment visibility"])[0])
    return f"For {atom.get('persona')}: lead with '{pain}' and back it with '{value}', then offer a 15-minute fit check or same-category case study."
