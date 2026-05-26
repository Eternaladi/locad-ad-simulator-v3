#!/usr/bin/env python3
from pathlib import Path
import argparse
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from locad_ad_simulator.improvement.feedback_ingest import append_feedback

parser = argparse.ArgumentParser(description="Append reviewer feedback for a validation run.")
parser.add_argument("--run-id", required=True)
parser.add_argument("--ad-id", required=True)
parser.add_argument("--reviewer", default="reviewer")
parser.add_argument("--useful", default="")
parser.add_argument("--wrong", default="")
parser.add_argument("--missing-context", default="")
parser.add_argument("--notes", default="")
args = parser.parse_args()
append_feedback(ROOT / "data/feedback/reviewer_labels.csv", {
    "run_id": args.run_id,
    "ad_id": args.ad_id,
    "reviewer": args.reviewer,
    "useful": args.useful,
    "wrong": args.wrong,
    "missing_context": args.missing_context,
    "notes": args.notes,
})
print("Feedback appended.")
