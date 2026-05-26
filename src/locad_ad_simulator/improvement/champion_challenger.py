from __future__ import annotations

from typing import Any


def compare_versions(champion: dict[str, Any], challenger: dict[str, Any]) -> dict[str, Any]:
    champion_score = float(champion.get("eval_score", 0))
    challenger_score = float(challenger.get("eval_score", 0))
    promote = challenger_score > champion_score + 0.02
    return {"promote": promote, "champion_score": champion_score, "challenger_score": challenger_score, "decision": "promote" if promote else "keep champion"}
