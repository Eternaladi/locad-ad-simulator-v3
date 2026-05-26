from __future__ import annotations

from pathlib import Path
from typing import Any
import json

from .icp_compiler import compile_icp_files


def load_icp_atoms(compiled_dir: Path, raw_dir: Path | None = None, auto_compile: bool = True) -> list[dict[str, Any]]:
    atoms_path = compiled_dir / "icp_atoms.jsonl"
    if not atoms_path.exists() and auto_compile:
        if raw_dir is None:
            raw_dir = compiled_dir.parent / "raw"
        compile_icp_files(raw_dir, compiled_dir)
    atoms: list[dict[str, Any]] = []
    with atoms_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                atoms.append(json.loads(line))
    return atoms


def load_axes(compiled_dir: Path) -> dict[str, list[str]]:
    path = compiled_dir / "icp_axes.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))
