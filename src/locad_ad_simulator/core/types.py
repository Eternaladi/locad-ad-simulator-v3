from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AdInput:
    copy_text: str
    copy_path: Path | None = None
    image_path: Path | None = None
    ad_id: str = "ad"


@dataclass(frozen=True)
class RunContext:
    run_id: str
    repo_root: Path
    run_dir: Path
    panel_name: str
    gate_name: str
    evaluator_version: str
    mode: str = "all"


@dataclass
class Scorecard:
    dimensions: dict[str, float]
    overall_score: float
    go_rate: float
    weak_rate: float
    no_go_rate: float
    verdict_breakdown: dict[str, int]
    confidence: dict[str, Any] = field(default_factory=dict)
