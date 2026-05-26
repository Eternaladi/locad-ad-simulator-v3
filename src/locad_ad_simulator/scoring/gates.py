from __future__ import annotations

from pathlib import Path
from typing import Any

from locad_ad_simulator.config import load_yaml


def decide_gate(scorecard: dict[str, Any], evidence_lint: dict[str, Any], gate_config_path: Path) -> dict[str, Any]:
    cfg = load_yaml(gate_config_path)
    avg = scorecard.get("avg_overall", 0)
    avg_scores = scorecard.get("avg_scores", {})
    high_risk = [v for v in evidence_lint.get("violated_rules", []) if v.get("severity") == "high"]
    go_rate = scorecard.get("go_rate", 0)
    reasons = []
    if avg < cfg["min_overall"]:
        reasons.append(f"overall {avg} below minimum {cfg['min_overall']}")
    if avg_scores.get("trust", 0) < cfg["min_trust"]:
        reasons.append(f"trust {avg_scores.get('trust', 0)} below minimum {cfg['min_trust']}")
    if avg_scores.get("proof_sufficiency", 0) < cfg["min_proof"]:
        reasons.append(f"proof sufficiency {avg_scores.get('proof_sufficiency', 0)} below minimum {cfg['min_proof']}")
    if len(high_risk) > cfg["max_high_risk_flags"]:
        reasons.append(f"{len(high_risk)} high-risk flags exceeds maximum {cfg['max_high_risk_flags']}")
    if go_rate < cfg["min_go_rate"]:
        reasons.append(f"GO rate {go_rate} below minimum {cfg['min_go_rate']}")

    if not reasons:
        verdict = "GO"
        reason = "Passes configured gate thresholds."
    elif avg >= cfg["min_overall"] - cfg.get("weak_band_delta", 0.6) and len(high_risk) <= cfg["max_high_risk_flags"]:
        verdict = "WEAK"
        reason = "Needs review: " + "; ".join(reasons)
    else:
        verdict = "NO-GO"
        reason = "Block before launch: " + "; ".join(reasons)
    return {"gate": cfg.get("name", gate_config_path.stem), "verdict": verdict, "reason": reason, "failed_checks": reasons, "exit_code": {"GO": 0, "WEAK": 1, "NO-GO": 2}[verdict]}
