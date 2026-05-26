from __future__ import annotations

from pathlib import Path
from typing import Any
import csv

from locad_ad_simulator.config import load_yaml


def load_csv_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_benchmarks(benchmarks_dir: Path) -> dict[str, Any]:
    bands_path = benchmarks_dir / "benchmark_bands.yaml"
    return {
        "ad_history": load_csv_rows(benchmarks_dir / "ad_history.csv"),
        "human_scores": load_csv_rows(benchmarks_dir / "human_scores.csv"),
        "campaign_outcomes": load_csv_rows(benchmarks_dir / "campaign_outcomes.csv"),
        "bands": load_yaml(bands_path).get("bands", {}) if bands_path.exists() else {},
    }
