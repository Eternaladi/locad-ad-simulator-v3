from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
import json

from locad_ad_simulator.config import write_json
from locad_ad_simulator.core.errors import DataValidationError

LIST_FIELDS = [
    "sales_channels", "top_pain_points", "locad_value_propositions", "key_motivations",
    "ad_creative_formats_that_resonate", "best_ad_channels", "likely_objections"
]

ATOM_FIELDS = [
    "icp_id", "persona", "persona_id", "region", "hq_location", "decision_maker_title", "age_range",
    "product_category", "sales_channels", "primary_marketplace", "revenue_stage", "annual_revenue_range",
    "employee_count", "top_pain_points", "locad_value_propositions", "key_motivations",
    "ad_creative_formats_that_resonate", "best_ad_channels", "likely_objections", "buying_trigger",
    "content_that_converts"
]


def _ensure_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    return [str(value)]


def normalize_icp(raw: dict[str, Any], source_file: str) -> dict[str, Any]:
    atom = {field: raw.get(field) for field in ATOM_FIELDS}
    for field in LIST_FIELDS:
        atom[field] = _ensure_list(atom.get(field))
    for key, default in {
        "icp_id": "unknown", "persona": "Unknown Persona", "persona_id": "UNKNOWN",
        "region": "Unknown", "product_category": "Unknown", "primary_marketplace": "Unknown",
        "revenue_stage": "Unknown", "decision_maker_title": "Unknown"
    }.items():
        if not atom.get(key):
            atom[key] = default
    atom["source_file"] = source_file
    atom["segment_label"] = f"{atom['region']} / {atom['persona']} / {atom['product_category']}"
    atom["evidence_id"] = atom["icp_id"]
    return atom


def compile_icp_files(raw_dir: Path, out_dir: Path) -> dict[str, Any]:
    if not raw_dir.exists():
        raise DataValidationError(f"Raw ICP directory not found: {raw_dir}")
    out_dir.mkdir(parents=True, exist_ok=True)
    atoms: list[dict[str, Any]] = []
    source_meta: list[dict[str, Any]] = []
    for path in sorted(raw_dir.glob("*.json")):
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if "icps" not in data:
            raise DataValidationError(f"{path.name} does not contain an 'icps' array")
        source_meta.append({"file": path.name, "meta": data.get("meta", {}), "count": len(data["icps"])})
        for raw in data["icps"]:
            atoms.append(normalize_icp(raw, path.name))
    if not atoms:
        raise DataValidationError(f"No ICP atoms compiled from {raw_dir}")

    atoms_path = out_dir / "icp_atoms.jsonl"
    with atoms_path.open("w", encoding="utf-8") as f:
        for atom in atoms:
            f.write(json.dumps(atom, ensure_ascii=False) + "\n")

    axes = build_axes(atoms)
    matrix = build_coverage_matrix(atoms)
    write_json(out_dir / "icp_axes.json", axes)
    write_json(out_dir / "coverage_matrix.json", matrix)
    write_json(out_dir / "compile_meta.json", {"total_atoms": len(atoms), "sources": source_meta})
    return {"total_atoms": len(atoms), "atoms_path": str(atoms_path), "axes": axes, "coverage_matrix": matrix}


def build_axes(atoms: list[dict[str, Any]]) -> dict[str, list[str]]:
    axes: dict[str, set[str]] = defaultdict(set)
    scalar_axes = ["region", "persona", "product_category", "primary_marketplace", "revenue_stage", "decision_maker_title"]
    list_axes = ["sales_channels", "top_pain_points", "locad_value_propositions", "likely_objections", "best_ad_channels"]
    for atom in atoms:
        for axis in scalar_axes:
            axes[axis].add(str(atom.get(axis, "Unknown")))
        for axis in list_axes:
            for value in atom.get(axis, []):
                axes[axis].add(str(value))
    return {axis: sorted(values) for axis, values in axes.items()}


def build_coverage_matrix(atoms: list[dict[str, Any]]) -> dict[str, Any]:
    counters: dict[str, Counter[str]] = {
        "region": Counter(), "persona": Counter(), "product_category": Counter(),
        "primary_marketplace": Counter(), "revenue_stage": Counter(), "sales_channels": Counter()
    }
    combo_counter: Counter[str] = Counter()
    for atom in atoms:
        for axis in ["region", "persona", "product_category", "primary_marketplace", "revenue_stage"]:
            counters[axis][str(atom.get(axis, "Unknown"))] += 1
        for channel in atom.get("sales_channels", []):
            counters["sales_channels"][channel] += 1
        combo_counter[f"{atom.get('region')} | {atom.get('persona')} | {atom.get('primary_marketplace')}"] += 1
    return {
        "counts": {axis: dict(counter.most_common()) for axis, counter in counters.items()},
        "top_region_persona_marketplace": dict(combo_counter.most_common(30)),
    }
