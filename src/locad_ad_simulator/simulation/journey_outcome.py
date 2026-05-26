from __future__ import annotations

from typing import Any


def decide_journey(internal_objections: list[dict[str, Any]], scorecard: dict[str, Any] | None = None) -> dict[str, Any]:
    blockers = [o for o in internal_objections if o.get("stance") == "blocker"]
    skeptical = [o for o in internal_objections if o.get("stance") == "skeptical"]
    if len(blockers) >= 3:
        result = "Would not request demo yet"
        reason = "Too many core stakeholders need proof before forwarding or booking."
    elif len(blockers) >= 1 or len(skeptical) >= 4:
        result = "Would save/forward, but not book yet"
        reason = "The ad has relevance but needs proof for internal objections."
    else:
        result = "Would likely request demo or fit check"
        reason = "The ad answers enough pains and proof needs to progress."
    return {"journey_result": result, "reason": reason, "blocker_count": len(blockers), "skeptical_count": len(skeptical)}
