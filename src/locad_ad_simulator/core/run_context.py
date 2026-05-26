from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re

from .types import RunContext


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "ad"


def create_run_context(repo_root: Path, ad_id: str, panel_name: str, gate_name: str, evaluator_version: str, mode: str) -> RunContext:
    stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    run_id = f"{stamp}_{slugify(ad_id)}"
    run_dir = repo_root / "runs" / run_id
    for sub in ["input_snapshot", "raw_llm", "parsed", "final"]:
        (run_dir / sub).mkdir(parents=True, exist_ok=True)
    return RunContext(run_id=run_id, repo_root=repo_root, run_dir=run_dir, panel_name=panel_name, gate_name=gate_name, evaluator_version=evaluator_version, mode=mode)
