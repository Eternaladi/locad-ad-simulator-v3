"""Market Fit Summary and market-aware report sections for Locad Ad Simulator v2.

Generates the structured output blocks that are added to the final validation report
when a --market flag is provided. Does not replace the base report — it supplements it.
"""
from __future__ import annotations

from typing import Any


def build_market_fit_summary(
    market_ctx: dict[str, Any],
    persona_scores: dict[str, Any],
    gate_decision: dict[str, Any],
    scorecard: dict[str, Any],
    ad_copy: str,
) -> dict[str, Any]:
    """Build the complete market-aware additions to the validation report.

    Returns a dict with all market-specific report sections.
    """
    market = market_ctx["market"]
    market_label = market_ctx["market_label"]
    icp_count = market_ctx["icp_count"]
    gate_overrides = market_ctx.get("gate_overrides", {})
    is_ramadan = market_ctx.get("is_ramadan", False)
    ramadan_relevant = market_ctx.get("ramadan_relevant", False)
    proof_gaps_required = market_ctx.get("proof_gaps_required", [])

    # ── gate check with market overrides ──────────────────────────────────────
    market_pass, market_gate_details = _evaluate_market_gate(
        scorecard, gate_decision, gate_overrides, market
    )

    # ── market proof gap analysis ─────────────────────────────────────────────
    proof_gap_analysis = _analyze_proof_gaps(ad_copy, proof_gaps_required, market)

    # ── marketplace mismatch ─────────────────────────────────────────────────
    from locad_ad_simulator.market.market_loader import check_marketplace_relevance, check_ramadan_gap
    marketplace_mismatches = check_marketplace_relevance(ad_copy, market)
    ramadan_check = check_ramadan_gap(ad_copy, market)

    # ── persona panel ─────────────────────────────────────────────────────────
    top_2 = persona_scores.get("top_2_resonant", [])
    strongest = persona_scores.get("strongest_match_label", "—")
    weakest = persona_scores.get("weakest_match_label", "—")
    blocker_objection = persona_scores.get("critical_blocker_objection", "")
    rewrite_rec = persona_scores.get("rewrite_recommendation", "")

    # ── plain-language verdict ────────────────────────────────────────────────
    verdict_line = _plain_language_verdict(
        market_label, gate_decision, scorecard, strongest, weakest
    )

    # ── non-technical summary (Suggestion D) ─────────────────────────────────
    non_technical_summary = _non_technical_summary(
        market_label, gate_decision, scorecard, strongest, weakest,
        blocker_objection, proof_gap_analysis
    )

    return {
        "market_context_header": {
            "market": market,
            "market_label": market_label,
            "icp_count": icp_count,
            "is_ramadan": is_ramadan,
            "ramadan_relevant": ramadan_relevant,
        },
        "market_gate": {
            "passed": market_pass,
            "overrides_applied": gate_overrides,
            "details": market_gate_details,
        },
        "proof_gap_analysis": proof_gap_analysis,
        "marketplace_mismatch": {
            "mismatches": marketplace_mismatches,
            "flag": bool(marketplace_mismatches),
            "detail": (
                f"Marketplaces mentioned in ad that are not relevant for {market_label}: "
                + ", ".join(marketplace_mismatches)
            ) if marketplace_mismatches else "No irrelevant marketplace mentions detected.",
        },
        "ramadan_check": ramadan_check,
        "persona_panel": persona_scores.get("panel", []),
        "strongest_persona": strongest,
        "weakest_persona": weakest,
        "top_2_resonant_personas": top_2,
        "critical_blocker_objection": blocker_objection,
        "rewrite_recommendation": rewrite_rec,
        "market_fit_verdict": verdict_line,
        "non_technical_summary": non_technical_summary,
    }


def _evaluate_market_gate(
    scorecard: dict[str, Any],
    gate_decision: dict[str, Any],
    gate_overrides: dict[str, Any],
    market: str,
) -> tuple[bool, dict[str, Any]]:
    """Check whether the ad passes market-specific gate thresholds."""
    if not gate_overrides:
        return gate_decision.get("verdict") == "GO", {"note": "No market-specific overrides for this gate config."}

    avg = scorecard.get("avg_overall", 0)
    go_rate = scorecard.get("go_rate", 0)
    avg_scores = scorecard.get("avg_scores", {})
    trust = avg_scores.get("trust", 0)
    localization = avg_scores.get("localization_fit", 0)

    failures = []
    min_overall = gate_overrides.get("min_overall")
    min_go_rate = gate_overrides.get("min_go_rate")
    min_trust = gate_overrides.get("min_trust")
    min_localization = gate_overrides.get("min_localization_fit")

    if min_overall and avg < min_overall:
        failures.append(f"Overall {avg} < market minimum {min_overall}")
    if min_go_rate and go_rate < min_go_rate:
        failures.append(f"GO rate {round(go_rate * 100)}% < market minimum {round(min_go_rate * 100)}%")
    if min_trust and trust < min_trust:
        failures.append(f"Trust {trust} < market minimum {min_trust} (critical for {gate_overrides.get('label', market)})")
    if min_localization and localization < min_localization:
        failures.append(f"Localization fit {localization} < market minimum {min_localization}")

    passed = len(failures) == 0
    return passed, {
        "thresholds_applied": {
            "min_overall": min_overall,
            "min_go_rate": min_go_rate,
            "min_trust": min_trust,
            "min_localization_fit": min_localization,
        },
        "failures": failures,
        "verdict": "PASS" if passed else "FAIL",
    }


def _analyze_proof_gaps(ad_copy: str, proof_gaps_required: list[str], market: str) -> dict[str, Any]:
    """Check which required proof points are missing from the ad."""
    copy_lower = ad_copy.lower()

    # Market-specific proof signals
    proof_signals: dict[str, list[str]] = {
        "usa": {
            "FBA migration proof or alternative proof of US brand migration": [
                "fba", "amazon fulfillment", "migrate", "migration", "switch from", "replace fba"
            ],
            "US warehouse SLA data (same-day or 3-day nationwide)": [
                "same-day", "3-day", "nationwide", "97.3", "98%", "us delivery", "coast to coast"
            ],
            "Multi-channel case study for US market": [
                "case study", "brand", "amazon", "shopify", "multi-channel", "omnichannel"
            ],
        },
        "gcc_uae": {
            "UAE or KSA cross-border fulfillment proof": [
                "uae", "ksa", "cross-border", "gcc", "saudi", "emirates"
            ],
            "Premium handling credentials for luxury or beauty": [
                "premium", "luxury", "white-glove", "temperature", "secure storage", "brand standards"
            ],
            "Free Trade Zone advantage mention": [
                "free trade zone", "ftz", "jafza", "freezone", "uae free"
            ],
            "Ramadan peak readiness (if in Ramadan period)": [
                "ramadan", "eid", "peak season", "gifting", "campaign readiness"
            ],
        },
        "gcc_ksa": {
            "KSA-specific delivery proof or SLA track record": [
                "ksa", "saudi", "riyadh", "jeddah", "khobar", "saudi arabia"
            ],
            "Noon, Zid, or Salla integration mention": [
                "noon", "zid", "salla"
            ],
            "Trust-first messaging for luxury or high-value SKUs": [
                "trust", "premium", "luxury", "secure", "white-glove", "high-value"
            ],
            "Ramadan peak readiness (if in Ramadan period)": [
                "ramadan", "eid", "peak season", "gifting"
            ],
        },
    }

    market_signals = proof_signals.get(market, {})
    present = []
    missing = []

    for gap_label in proof_gaps_required:
        keywords = market_signals.get(gap_label, [])
        if keywords and any(k in copy_lower for k in keywords):
            present.append(gap_label)
        else:
            missing.append(gap_label)

    return {
        "market": market,
        "required_count": len(proof_gaps_required),
        "present": present,
        "missing": missing,
        "coverage_pct": round(len(present) / len(proof_gaps_required) * 100) if proof_gaps_required else 100,
    }


def _plain_language_verdict(
    market_label: str,
    gate_decision: dict[str, Any],
    scorecard: dict[str, Any],
    strongest: str,
    weakest: str,
) -> str:
    """One-line verdict in plain language for a non-technical stakeholder."""
    verdict = gate_decision.get("verdict", "UNKNOWN")
    score = scorecard.get("avg_overall", 0)
    go_rate = round(scorecard.get("go_rate", 0) * 100)
    emoji = {"GO": "✅", "WEAK": "⚠️", "NO-GO": "❌"}.get(verdict, "")

    if verdict == "GO":
        return (
            f"{emoji} Ready for {market_label}: Overall {score}/10, {go_rate}% GO. "
            f"Resonates most with {strongest}. Review {weakest} messaging before final launch."
        )
    elif verdict == "WEAK":
        return (
            f"{emoji} Needs revision for {market_label}: Overall {score}/10, {go_rate}% GO. "
            f"Works for {strongest} but fails to convince {weakest}. Fix proof gaps before spending."
        )
    else:
        return (
            f"{emoji} Do not launch for {market_label}: Overall {score}/10, {go_rate}% GO. "
            f"Critical gaps prevent this ad from working with {weakest}. Revise before any spend."
        )


def _non_technical_summary(
    market_label: str,
    gate_decision: dict[str, Any],
    scorecard: dict[str, Any],
    strongest: str,
    weakest: str,
    blocker_objection: str,
    proof_gap_analysis: dict[str, Any],
) -> str:
    """3-sentence plain-language summary for a marketing manager or CEO."""
    verdict = gate_decision.get("verdict", "UNKNOWN")
    score = scorecard.get("avg_overall", 0)
    go_rate = round(scorecard.get("go_rate", 0) * 100)
    missing = proof_gap_analysis.get("missing", [])

    # Sentence 1: verdict and score
    if verdict == "GO":
        s1 = f"This ad scores {score}/10 for {market_label} with {go_rate}% of simulated buyers ready to engage — it is ready to test."
    elif verdict == "WEAK":
        s1 = f"This ad scores {score}/10 for {market_label} with {go_rate}% of simulated buyers engaging — it needs revisions before paid spend."
    else:
        s1 = f"This ad scores {score}/10 for {market_label} with only {go_rate}% of simulated buyers engaging — do not spend on this version."

    # Sentence 2: what the ad does well
    s2 = f"The strongest response comes from the {strongest} persona, who sees relevance in the value proposition and messaging."

    # Sentence 3: most important fix
    if missing:
        top_missing = missing[0]
        s3 = f"The single most important fix before launch: add {top_missing} — this is the primary blocker for the {weakest} persona."
    elif blocker_objection:
        short_objection = blocker_objection[:120] + ("..." if len(blocker_objection) > 120 else "")
        s3 = f"The single most important fix: address the {weakest} persona's concern — \"{short_objection}\""
    else:
        s3 = f"Before increasing spend, address the {weakest} persona's messaging gap to improve overall resonance."

    return f"{s1} {s2} {s3}"


# ── markdown rendering ─────────────────────────────────────────────────────────

def render_market_sections_markdown(market_fit: dict[str, Any]) -> list[str]:
    """Return a list of markdown lines for all market-aware report sections."""
    lines: list[str] = []

    # Non-technical summary at the very top
    summary = market_fit.get("non_technical_summary", "")
    if summary:
        lines += [
            "---",
            "## 📋 Executive Summary",
            "",
            f"> {summary}",
            "",
            "---",
            "",
        ]

    # Market context header
    ctx = market_fit.get("market_context_header", {})
    lines += [
        "## 🌍 Market Context",
        "",
        f"**Market validated against:** {ctx.get('market_label', '—')}  ",
        f"**ICP accounts in panel:** {ctx.get('icp_count', 0)}  ",
    ]
    if ctx.get("ramadan_relevant"):
        ramadan_status = "⭐ Active — Ramadan period in effect" if ctx.get("is_ramadan") else "Not currently active"
        lines.append(f"**Ramadan context:** {ramadan_status}  ")
    lines.append("")

    # Market gate result
    mgate = market_fit.get("market_gate", {})
    gate_verdict = mgate.get("details", {}).get("verdict", "UNKNOWN")
    gate_emoji = "✅" if gate_verdict == "PASS" else "❌"
    lines += [
        f"### {gate_emoji} Market Gate: {gate_verdict}",
        "",
    ]
    thresholds = mgate.get("details", {}).get("thresholds_applied", {})
    if thresholds:
        lines.append("| Threshold | Required |")
        lines.append("|---|---:|")
        for k, v in thresholds.items():
            if v is not None:
                lines.append(f"| {k.replace('_', ' ').title()} | {v} |")
    failures = mgate.get("details", {}).get("failures", [])
    if failures:
        lines.append("\n**Gate failures:**")
        for f in failures:
            lines.append(f"- {f}")
    lines.append("")

    # Marketplace mismatch
    mismatch = market_fit.get("marketplace_mismatch", {})
    if mismatch.get("flag"):
        lines += [
            "### ⚠️ Marketplace Mismatch",
            "",
            mismatch.get("detail", ""),
            "",
        ]

    # Ramadan check
    ramadan = market_fit.get("ramadan_check", {})
    if ramadan.get("active") and ramadan.get("flag"):
        lines += [
            "### 🌙 Ramadan Localization Gap",
            "",
            ramadan.get("detail", ""),
            "",
        ]

    # Market-specific proof gap analysis
    pga = market_fit.get("proof_gap_analysis", {})
    lines += [
        "## 🔍 Market-Specific Proof Gap Analysis",
        "",
        f"**Coverage:** {pga.get('coverage_pct', 0)}% of required market proof points present  ",
        f"**Present ({len(pga.get('present', []))}):** {', '.join(pga.get('present', [])) or 'None'}  ",
        f"**Missing ({len(pga.get('missing', []))}):**",
        "",
    ]
    for gap in pga.get("missing", []) or ["None — all required proof points present."]:
        lines.append(f"- ❌ {gap}")
    lines.append("")

    # Buyer persona reaction panel
    lines += [
        "## 👥 Buyer Persona Reaction Panel",
        "",
        "| Persona | Stance | Resonance | Reaction | Top Objection |",
        "|---|---|---:|---|---|",
    ]
    for p in market_fit.get("persona_panel", []):
        stance_emoji = {"GO": "✅", "SKEPTICAL": "⚠️", "BLOCKER": "❌"}.get(p.get("stance", ""), "")
        reaction_short = p.get("reaction", "")[:60] + ("..." if len(p.get("reaction", "")) > 60 else "")
        objection_short = p.get("primary_objection", "")[:60] + ("..." if len(p.get("primary_objection", "")) > 60 else "")
        lines.append(
            f"| {p.get('role')} | {stance_emoji} {p.get('stance')} | {p.get('resonance_score')}/10 "
            f"| {reaction_short} | {objection_short} |"
        )
    lines.append("")

    # Strongest and weakest persona
    lines += [
        f"**Strongest persona match:** {market_fit.get('strongest_persona', '—')}  ",
        f"**Critical blocker persona:** {market_fit.get('weakest_persona', '—')}  ",
        f"**Top 2 resonant personas:** {', '.join(market_fit.get('top_2_resonant_personas', []))}  ",
        "",
        f"**Critical blocker objection:** {market_fit.get('critical_blocker_objection', '—')}",
        "",
    ]

    # Rewrite recommendation
    rewrite = market_fit.get("rewrite_recommendation", "")
    if rewrite:
        lines += [
            "## ✏️ Rewrite Recommendation",
            "",
            "```",
            rewrite,
            "```",
            "",
        ]

    # Market Fit Summary (final verdict block)
    lines += [
        "## 📊 Market Fit Summary",
        "",
        f"| | |",
        "|---|---|",
        f"| **Market** | {ctx.get('market_label', '—')} |",
        f"| **ICP panel size** | {ctx.get('icp_count', 0)} accounts |",
        f"| **Top 2 personas resonated** | {', '.join(market_fit.get('top_2_resonant_personas', ['—']))} |",
        f"| **Critical blocker persona** | {market_fit.get('weakest_persona', '—')} |",
        f"| **Blocker's primary objection** | {market_fit.get('critical_blocker_objection', '—')[:80]} |",
        f"| **Market gate** | {gate_emoji} {gate_verdict} |",
        "",
        f"**Verdict:** {market_fit.get('market_fit_verdict', '—')}",
        "",
    ]

    return lines
