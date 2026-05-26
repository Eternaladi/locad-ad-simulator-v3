from __future__ import annotations

from typing import Any


def summarize_variant_diff(reports: list[dict[str, Any]]) -> dict[str, Any]:
    ranked = sorted(reports, key=lambda r: r.get("final_scorecard", {}).get("avg_overall", 0), reverse=True)
    return {"winner": ranked[0].get("meta", {}).get("ad_id") if ranked else None, "ranked_ad_ids": [r.get("meta", {}).get("ad_id") for r in ranked]}
