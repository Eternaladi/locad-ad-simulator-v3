from __future__ import annotations

from typing import Any


def evaluate_localization(ad_copy: str, rules: dict[str, Any], panel: list[dict[str, Any]]) -> dict[str, Any]:
    lower = ad_copy.lower()
    regions = sorted({a.get("region") for a in panel})
    checks = []
    for region in regions:
        cfg = rules.get("localization_rules", {}).get("regions", {}).get(region, {})
        preferred = [t for t in cfg.get("preferred_terms", []) if t.lower() in lower]
        missing_pref = [t for t in cfg.get("preferred_terms", []) if t.lower() not in lower][:5]
        checks.append({"region": region, "matched_terms": preferred, "missing_example_terms": missing_pref, "score": min(10, 4 + len(preferred) * 1.5)})
    avg = round(sum(c["score"] for c in checks) / len(checks), 1) if checks else 5.0
    return {"average_localization_score": avg, "region_checks": checks}
