from locad_ad_simulator.scoring.aggregate import aggregate_persona_results
from locad_ad_simulator.scoring.gates import decide_gate
from pathlib import Path


def test_aggregate_and_gate():
    rows = []
    for i in range(10):
        rows.append({"scores": {"relevance": 8, "pain_resonance": 8, "value_prop_alignment": 8, "trust": 7, "clarity": 8, "cta_pull": 7, "localization_fit": 7, "proof_sufficiency": 7}, "overall_score": 7.5, "verdict": "GO"})
    score = aggregate_persona_results(rows)
    assert score["avg_overall"] >= 7
    gate = decide_gate(score, {"violated_rules": []}, Path(__file__).resolve().parents[1] / "configs/gates/standard.yaml")
    assert gate["verdict"] == "GO"
