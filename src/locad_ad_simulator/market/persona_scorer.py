"""Buyer persona scoring layer for Locad Ad Simulator v2.

Evaluates an ad copy through the lens of each of the 6 Locad buyer personas and
returns a per-persona breakdown: simulated reaction, stance (GO / SKEPTICAL / BLOCKER),
primary objection or proof gap, and a numeric resonance score.

This runs in parallel to the ICP scoring and does not replace or modify the
deterministic scoring engine — it is an additive evaluation layer.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# ── helpers ────────────────────────────────────────────────────────────────────

def _keyword_hit_rate(ad_copy: str, signals: list[str]) -> float:
    """Return fraction of scoring signals present in the ad copy (case-insensitive)."""
    if not signals:
        return 0.0
    copy_lower = ad_copy.lower()
    hits = sum(1 for s in signals if s.lower() in copy_lower)
    return hits / len(signals)


def _red_flag_count(ad_copy: str, red_flags: list[str]) -> int:
    """Count how many red-flag patterns are triggered in the ad copy."""
    copy_lower = ad_copy.lower()
    # Each red flag string is interpreted as a concept — match on key words
    count = 0
    red_flag_keywords = {
        "overly technical ops language with no strategic framing": ["warehouse", "fulfillment center", "3pl", "pick and pack"],
        "pure cost savings pitch without growth angle": [],  # detected by absence
        "vague fast delivery language without sla specifics": ["fast delivery", "quick shipping", "speedy"],
        "no mention of ops outcomes or accuracy metrics": [],
        "pitching only cheap shipping without campaign or cx angle": ["cheap shipping", "lowest rate"],
        "ignoring review and ratings impact": [],
        "technical ops language without financial outcome": [],
        "vague cost claims without specific proof or percentage": [],
        "pure backend ops pitch with no marketing or conversion outcome": [],
        "growth and expansion language with no cx outcome mentioned": [],
    }
    for flag_text in red_flags:
        flag_lower = flag_text.lower()
        for key, kws in red_flag_keywords.items():
            if key in flag_lower and kws:
                if any(k in copy_lower for k in kws):
                    count += 1
    return count


def _simulated_reaction(persona: dict[str, Any], hit_rate: float, red_flag_hit: int) -> str:
    """Generate a one-line simulated reaction for the persona."""
    role = persona["role"]
    hook = persona["messaging_hook"]

    if hit_rate >= 0.35 and red_flag_hit == 0:
        return f"This resonates — I see the angle around {_top_signal(persona)}. I'd book a demo."
    elif hit_rate >= 0.20:
        return f"Somewhat interesting but I'd want to see proof of {_top_proof_ask(persona)}."
    elif red_flag_hit > 0:
        return f"This misses me — the framing doesn't speak to what drives my decisions as {role}."
    else:
        return f"Not compelling enough. I need to see: {_top_proof_ask(persona)}."


def _top_signal(persona: dict[str, Any]) -> str:
    signals = persona.get("scoring_signals", [])
    return signals[0] if signals else "strategic impact"


def _top_proof_ask(persona: dict[str, Any]) -> str:
    objections = persona.get("objection_patterns", [])
    return objections[0] if objections else "specific proof points"


def _derive_stance(hit_rate: float, red_flag_hit: int) -> str:
    if hit_rate >= 0.35 and red_flag_hit == 0:
        return "GO"
    elif hit_rate >= 0.18 and red_flag_hit <= 1:
        return "SKEPTICAL"
    else:
        return "BLOCKER"


def _primary_objection(persona: dict[str, Any], hit_rate: float, ad_copy: str) -> str:
    """Return the most likely objection this persona would raise before booking a demo."""
    objections = persona.get("objection_patterns", [])
    if not objections:
        return "No specific proof provided for my key concerns."

    copy_lower = ad_copy.lower()
    # Return the first objection whose keywords aren't addressed in the copy
    for objection in objections:
        # Simple heuristic: if the objection key terms are absent, it's the blocker
        key_terms = [w for w in objection.lower().split() if len(w) > 4]
        if not any(t in copy_lower for t in key_terms):
            return objection

    return objections[0]  # fallback to first


def _resonance_score(hit_rate: float, red_flag_hit: int) -> float:
    """Produce a 0–10 resonance score for this persona."""
    base = min(hit_rate * 28.0, 10.0)  # scale hit rate to 0–10
    base = max(base, 1.0)
    penalty = red_flag_hit * 1.2
    return round(max(1.0, min(10.0, base - penalty)), 1)


# ── public API ─────────────────────────────────────────────────────────────────

def load_buyer_personas(repo_root: Path) -> list[dict[str, Any]]:
    """Load buyer personas from data/personas/buyer_personas.json."""
    personas_path = repo_root / "data/personas/buyer_personas.json"
    if not personas_path.exists():
        return []
    with personas_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("personas", [])


def score_buyer_personas(
    ad_copy: str,
    repo_root: Path,
) -> dict[str, Any]:
    """Evaluate ad copy against all 6 buyer personas.

    Returns:
      panel: list of per-persona result dicts
      strongest_match: persona_id with highest resonance
      weakest_match: persona_id with lowest resonance (most critical blocker)
      strongest_match_label: human-readable role label
      weakest_match_label: human-readable role label
      top_2_resonant: list of top 2 persona role labels
      critical_blocker_objection: primary objection from the weakest persona
      rewrite_recommendation: one specific rewrite suggestion for the weakest persona
    """
    personas = load_buyer_personas(repo_root)
    if not personas:
        return {
            "panel": [],
            "strongest_match": None,
            "weakest_match": None,
            "strongest_match_label": "Unknown",
            "weakest_match_label": "Unknown",
            "top_2_resonant": [],
            "critical_blocker_objection": "No personas loaded.",
            "rewrite_recommendation": "Load buyer personas data to enable this feature.",
        }

    panel = []
    for persona in personas:
        hit_rate = _keyword_hit_rate(ad_copy, persona.get("scoring_signals", []))
        red_flag_hit = _red_flag_count(ad_copy, persona.get("red_flags", []))
        stance = _derive_stance(hit_rate, red_flag_hit)
        reaction = _simulated_reaction(persona, hit_rate, red_flag_hit)
        objection = _primary_objection(persona, hit_rate, ad_copy)
        score = _resonance_score(hit_rate, red_flag_hit)

        panel.append({
            "persona_id": persona["persona_id"],
            "role": persona["role"],
            "stance": stance,
            "resonance_score": score,
            "reaction": reaction,
            "primary_objection": objection,
            "messaging_hook": persona["messaging_hook"],
            "hit_rate": round(hit_rate, 3),
            "red_flag_count": red_flag_hit,
        })

    # Sort by resonance score
    panel_sorted = sorted(panel, key=lambda p: p["resonance_score"], reverse=True)
    strongest = panel_sorted[0] if panel_sorted else None
    weakest = panel_sorted[-1] if panel_sorted else None

    top_2 = [p["role"] for p in panel_sorted[:2]]

    rewrite_rec = _rewrite_recommendation(weakest, ad_copy) if weakest else ""

    return {
        "panel": panel,
        "strongest_match": strongest["persona_id"] if strongest else None,
        "weakest_match": weakest["persona_id"] if weakest else None,
        "strongest_match_label": strongest["role"] if strongest else "Unknown",
        "weakest_match_label": weakest["role"] if weakest else "Unknown",
        "top_2_resonant": top_2,
        "critical_blocker_objection": weakest["primary_objection"] if weakest else "",
        "rewrite_recommendation": rewrite_rec,
    }


def _rewrite_recommendation(weakest_persona: dict[str, Any], ad_copy: str) -> str:
    """Suggest a specific rewrite for the headline/opening line based on the weakest persona's top pain."""
    if not weakest_persona:
        return ""
    role = weakest_persona["role"]
    hook = weakest_persona["messaging_hook"]
    objection = weakest_persona["primary_objection"]

    # Extract first line of ad copy as the "headline"
    lines = [l.strip() for l in ad_copy.strip().splitlines() if l.strip()]
    current_headline = lines[0] if lines else "(no headline detected)"

    return (
        f"Current opening: \"{current_headline[:80]}{'...' if len(current_headline) > 80 else ''}\"\n"
        f"Weakest persona: {role} — their top concern: {objection}\n"
        f"Suggested reframe: Lead with the outcome {role} cares most about. "
        f"Consider opening with something closer to: \"{hook}\""
    )
