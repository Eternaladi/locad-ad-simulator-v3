from __future__ import annotations

from pathlib import Path
from typing import Any

from .scorecard import bar


def write_markdown_report(report: dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    meta = report["meta"]
    score = report["final_scorecard"]
    gate = report["gate_decision"]
    coverage = report["coverage"]
    lint = report["icp_alignment"]
    committee = report["committee_simulation"]
    diff = report["differential_value"]
    market_fit = report.get("market_fit", {})
    emoji = {"GO": "✅", "WEAK": "⚠️", "NO-GO": "❌"}.get(gate["verdict"], "")

    lines: list[str] = ["# Locad Ad Validation Report", ""]

    # ── Non-technical executive summary (Suggestion D) — always at the top ──
    if market_fit:
        from locad_ad_simulator.market.market_report import render_market_sections_markdown
        exec_summary = market_fit.get("non_technical_summary", "")
        if exec_summary:
            lines += [
                "---",
                "## 📋 Executive Summary",
                "",
                f"> {exec_summary}",
                "",
                "---",
                "",
            ]

    # ── Run metadata ────────────────────────────────────────────────────────
    lines += [
        f"**Run ID:** `{meta['run_id']}`  ",
        f"**Ad:** `{meta.get('ad_id')}`  ",
        f"**Panel:** `{meta['panel']}`  ",
        f"**Gate:** `{gate['gate']}`  ",
        f"**Evaluator:** `{meta['evaluator_version']}`  ",
    ]
    if meta.get("market"):
        market_label = market_fit.get("market_context_header", {}).get("market_label", meta["market"])
        icp_count = market_fit.get("market_context_header", {}).get("icp_count", "?")
        lines.append(f"**Market:** `{market_label}` ({icp_count} ICPs in panel)  ")
    lines += ["", f"## {emoji} Gate verdict: {gate['verdict']}", "", gate["reason"], ""]

    # ── Market Context block (right after gate verdict, when market is set) ─
    if market_fit:
        ctx = market_fit.get("market_context_header", {})
        gate_details = market_fit.get("market_gate", {}).get("details", {})
        mgate_verdict = gate_details.get("verdict", "—")
        mgate_emoji = "✅" if mgate_verdict == "PASS" else "❌"

        lines += [
            "## 🌍 Market Context",
            "",
            f"**Market validated against:** {ctx.get('market_label', '—')}  ",
            f"**ICP accounts in panel:** {ctx.get('icp_count', 0)}  ",
        ]
        if ctx.get("ramadan_relevant"):
            ramadan_status = "⭐ **Active** — Ramadan period in effect" if ctx.get("is_ramadan") else "Not currently active"
            lines.append(f"**Ramadan context:** {ramadan_status}  ")
        lines += ["", f"### {mgate_emoji} Market Gate: {mgate_verdict}", ""]

        thresholds = gate_details.get("thresholds_applied", {})
        if thresholds:
            lines += ["| Threshold | Required |", "|---|---:|"]
            for k, v in thresholds.items():
                if v is not None:
                    lines.append(f"| {k.replace('_', ' ').title()} | {v} |")
        failures = gate_details.get("failures", [])
        if failures:
            lines += ["", "**Market gate failures:**"]
            for f in failures:
                lines.append(f"- ❌ {f}")
        lines.append("")

        # Ramadan gap flag
        ramadan_check = market_fit.get("ramadan_check", {})
        if ramadan_check.get("active") and ramadan_check.get("flag"):
            lines += [
                "### 🌙 Ramadan Localization Gap",
                "",
                f"> {ramadan_check.get('detail', '')}",
                "",
            ]

        # Marketplace mismatch flag
        mismatch = market_fit.get("marketplace_mismatch", {})
        if mismatch.get("flag"):
            lines += [
                "### ⚠️ Marketplace Mismatch Detected",
                "",
                f"> {mismatch.get('detail', '')}",
                "",
            ]

    # ── Scorecard ────────────────────────────────────────────────────────────
    lines += [
        "## Scorecard",
        "",
        f"**Overall:** {bar(score['avg_overall'])} **{score['avg_overall']} / 10**  ",
        f"**GO rate:** {round(score.get('go_rate', 0) * 100)}%  ",
        f"**Confidence:** {score.get('confidence', {}).get('level', 'unknown')} ({score.get('confidence', {}).get('overall_stdev', '–')} stdev)",
        "",
        "| Dimension | Avg |",
        "|---|---:|",
    ]
    for dim, val in score.get("avg_scores", {}).items():
        lines.append(f"| {dim.replace('_', ' ').title()} | {bar(val)} {val} |")

    # ── ICP coverage ─────────────────────────────────────────────────────────
    lines += [
        "",
        "## ICP coverage",
        "",
        f"Coverage score: **{coverage.get('coverage_score')}** across `{', '.join(coverage.get('required_axes', []))}`.",
        "",
    ]
    if coverage.get("missing_segments"):
        lines.append("Likely missed segments:")
        for segment in coverage["missing_segments"][:6]:
            lines.append(f"- {segment}")

    # ── Evidence-grounded linter ─────────────────────────────────────────────
    lines += [
        "",
        "## Evidence-grounded linter",
        "",
        f"**Summary:** {lint.get('summary')}",
        "",
        "**Matched ICP pain points:**",
    ]
    for p in lint.get("matched_pain_points", [])[:5] or ["No strong pain-point match."]:
        lines.append(f"- {p}")
    lines.append("\n**Matched Locad value props:**")
    for v in lint.get("matched_value_props", [])[:5] or ["No strong value-prop match."]:
        lines.append(f"- {v}")
    lines.append("\n**Missing proof:**")
    for m in lint.get("missing_proof", []) or ["No major missing proof detected by current rules."]:
        lines.append(f"- {m}")
    lines.append("\n**Rule violations:**")
    for v in lint.get("violated_rules", []) or [{"id": "none", "reason": "No rule violations detected."}]:
        lines.append(f"- `{v.get('id')}` ({v.get('severity', 'info')}): {v.get('reason')} — {v.get('evidence', '')}")

    # ── Market-specific proof gap analysis ───────────────────────────────────
    if market_fit:
        pga = market_fit.get("proof_gap_analysis", {})
        lines += [
            "",
            "## 🔍 Market-Specific Proof Gap Analysis",
            "",
            f"**Coverage:** {pga.get('coverage_pct', 0)}% of required market proof points present  ",
        ]
        present_list = pga.get("present", [])
        missing_list = pga.get("missing", [])
        if present_list:
            lines.append(f"**Present:** {', '.join(present_list)}  ")
        lines.append(f"**Missing ({len(missing_list)}):**")
        lines.append("")
        for gap in missing_list or ["None — all required proof points present."]:
            lines.append(f"- ❌ {gap}")

    # ── Buying committee simulation ───────────────────────────────────────────
    lines += [
        "",
        "## Buying committee simulation",
        "",
        f"**Journey outcome:** {committee.get('journey_result')}",
        "",
        f"Reason: {committee.get('reason')}",
        "",
        "| Role | Stance | Objection |",
        "|---|---|---|",
    ]
    for o in committee.get("internal_objections", []):
        lines.append(f"| {o.get('role')} | {o.get('stance')} | {o.get('objection')} |")

    # ── Buyer persona reaction panel ─────────────────────────────────────────
    if market_fit and market_fit.get("persona_panel"):
        lines += [
            "",
            "## 👥 Buyer Persona Reaction Panel",
            "",
            "| Persona | Stance | Resonance | Reaction | Top Objection |",
            "|---|---|---:|---|---|",
        ]
        for p in market_fit["persona_panel"]:
            stance_emoji = {"GO": "✅", "SKEPTICAL": "⚠️", "BLOCKER": "❌"}.get(p.get("stance", ""), "")
            reaction_short = (p.get("reaction", "")[:65] + "...") if len(p.get("reaction", "")) > 65 else p.get("reaction", "")
            obj_short = (p.get("primary_objection", "")[:65] + "...") if len(p.get("primary_objection", "")) > 65 else p.get("primary_objection", "")
            lines.append(
                f"| {p.get('role')} | {stance_emoji} {p.get('stance')} | {p.get('resonance_score')}/10 "
                f"| {reaction_short} | {obj_short} |"
            )
        lines += [
            "",
            f"**Strongest persona match:** {market_fit.get('strongest_persona', '—')}  ",
            f"**Critical blocker persona:** {market_fit.get('weakest_persona', '—')}  ",
            f"**Top 2 resonant personas:** {', '.join(market_fit.get('top_2_resonant_personas', []))}  ",
            "",
            f"**Blocker's primary objection:** {market_fit.get('critical_blocker_objection', '—')}",
        ]

    # ── Rewrite recommendation ────────────────────────────────────────────────
    rewrite = market_fit.get("rewrite_recommendation", "") if market_fit else ""
    if rewrite:
        lines += [
            "",
            "## ✏️ Rewrite Recommendation",
            "",
            "```",
            rewrite,
            "```",
        ]

    # ── Added value over generic ChatGPT ─────────────────────────────────────
    lines += [
        "",
        "## Added value over generic ChatGPT",
        "",
        "Generic baseline would likely say:",
    ]
    for f in diff.get("generic_baseline_findings", []):
        lines.append(f"- {f}")
    lines.append("\nLocad validator additionally found:")
    for f in diff.get("locad_validator_additions", []):
        lines.append(f"- {f}")

    # ── Representative persona reactions (ICP-level) ──────────────────────────
    lines += [
        "",
        "## Representative persona reactions",
        "",
    ]
    for r in report.get("persona_results", [])[:8]:
        lines += [
            f"### {r.get('verdict')} — {r.get('icp_id')} / {r.get('persona')} / {r.get('region')}",
            "",
            f"> {r.get('first_reaction')}",
            "",
            f"Overall: **{r.get('overall_score')} / 10**  ",
            f"Suggestion: {r.get('copy_suggestion')}",
            "",
        ]

    # ── Market Fit Summary (final block) ─────────────────────────────────────
    if market_fit:
        ctx = market_fit.get("market_context_header", {})
        gate_details = market_fit.get("market_gate", {}).get("details", {})
        mgate_verdict = gate_details.get("verdict", "—")
        mgate_emoji = "✅" if mgate_verdict == "PASS" else "❌"
        top_2 = market_fit.get("top_2_resonant_personas", [])
        blocker_obj = market_fit.get("critical_blocker_objection", "—")
        verdict_line = market_fit.get("market_fit_verdict", "")

        lines += [
            "## 📊 Market Fit Summary",
            "",
            "| | |",
            "|---|---|",
            f"| **Market** | {ctx.get('market_label', '—')} |",
            f"| **ICP panel size** | {ctx.get('icp_count', 0)} accounts |",
            f"| **Top 2 personas resonated** | {', '.join(top_2) if top_2 else '—'} |",
            f"| **Critical blocker persona** | {market_fit.get('weakest_persona', '—')} |",
            f"| **Blocker's primary objection** | {blocker_obj[:90] + '...' if len(blocker_obj) > 90 else blocker_obj} |",
            f"| **Market gate result** | {mgate_emoji} {mgate_verdict} |",
            "",
            f"**One-line verdict:** {verdict_line}",
            "",
        ]

    # ── Recommended next actions ──────────────────────────────────────────────
    lines += ["## Recommended next actions", ""]
    for action in report.get("next_actions", []):
        lines.append(f"- {action}")

    path.write_text("\n".join(lines), encoding="utf-8")
    return path
