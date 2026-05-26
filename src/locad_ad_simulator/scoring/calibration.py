from __future__ import annotations

from pathlib import Path
from typing import Any
import csv
import yaml


def rebuild_benchmark_bands(ad_history_csv: Path, output_yaml: Path) -> dict[str, Any]:
    rows = []
    if ad_history_csv.exists():
        with ad_history_csv.open("r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    metrics = ["overall_score", "trust", "proof_sufficiency"]
    bands: dict[str, Any] = {}
    for metric in metrics:
        vals = sorted(float(r[metric]) for r in rows if r.get(metric))
        if not vals:
            continue
        def pct(p: float) -> float:
            idx = min(len(vals) - 1, max(0, round((len(vals) - 1) * p)))
            return round(vals[idx], 2)
        bands[metric] = {"top": pct(0.8), "strong": pct(0.6), "average": pct(0.4), "weak": pct(0.2)}
    output_yaml.write_text(yaml.safe_dump({"bands": bands}, sort_keys=False), encoding="utf-8")
    return {"bands": bands, "output": str(output_yaml)}
