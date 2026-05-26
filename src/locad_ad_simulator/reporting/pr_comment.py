from __future__ import annotations

from pathlib import Path
from typing import Any


def write_pr_comment(report: dict[str, Any], path: Path) -> Path:
    gate = report["gate_decision"]
    score = report["final_scorecard"]
    lint = report["icp_alignment"]
    lines = [
        f"## Locad Ad Validator: {gate['verdict']}",
        "",
        f"Overall: **{score['avg_overall']} / 10** | GO rate: **{round(score.get('go_rate', 0) * 100)}%** | Gate: `{gate['gate']}`",
        "",
        gate["reason"],
        "",
        "### Top proof gaps",
    ]
    for gap in lint.get("missing_proof", [])[:4] or ["No major proof gaps detected."]:
        lines.append(f"- {gap}")
    lines.append("\n### Locad-specific additions over generic ChatGPT")
    for item in report.get("differential_value", {}).get("locad_validator_additions", [])[:5]:
        lines.append(f"- {item}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
