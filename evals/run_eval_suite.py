#!/usr/bin/env python3
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from locad_ad_simulator.cli import run_validation

report = run_validation(
    repo_root=ROOT,
    image_path=Path("inputs/ads/sample_locad_ad.png"),
    copy_path=Path("inputs/ads/sample_locad_ad_copy.txt"),
    panel_name="usa_gcc_balanced",
    gate_name="standard",
    mode="all",
)
summary = {
    "run_id": report["meta"]["run_id"],
    "verdict": report["gate_decision"]["verdict"],
    "overall": report["final_scorecard"]["avg_overall"],
    "coverage": report["coverage"]["coverage_score"],
}
print(json.dumps(summary, indent=2))
assert report["coverage"]["panel_size"] > 0
assert report["icp_alignment"]["icp_evidence_refs"]
assert report["differential_value"]["locad_validator_additions"]
