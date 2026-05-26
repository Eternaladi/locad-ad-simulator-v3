from __future__ import annotations

from typing import Any

from .committee_roles import COMMITTEE_ROLES


def role_objections(ad_copy: str, evidence_lint: dict[str, Any]) -> list[dict[str, Any]]:
    lower = ad_copy.lower()
    missing = evidence_lint.get("missing_proof", [])
    matched_objections = evidence_lint.get("matched_objections", [])
    out = []
    for role in COMMITTEE_ROLES:
        cares = role["cares_about"]
        role_specific_missing = [g for g in missing if any(c.lower() in g.lower() for c in cares)]
        role_specific_objection = [o for o in matched_objections if any(c.lower() in o.lower() for c in cares)]
        concern = role_specific_objection[0] if role_specific_objection else (role_specific_missing[0] if role_specific_missing else role["default_objection"])
        stance = "support" if any(c.lower() in lower for c in cares) and not role_specific_missing else "blocker" if role_specific_missing else "skeptical"
        out.append({"role": role["role"], "stance": stance, "objection": concern})
    return out
