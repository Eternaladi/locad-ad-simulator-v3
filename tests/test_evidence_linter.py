from pathlib import Path

from locad_ad_simulator.ingest.brand_loader import load_brand_context
from locad_ad_simulator.ingest.icp_loader import load_icp_atoms
from locad_ad_simulator.ingest.rules_loader import load_rules
from locad_ad_simulator.panels.panel_builder import build_panel
from locad_ad_simulator.evaluators.evidence_linter import lint_ad_evidence


def test_linter_returns_traceable_refs():
    root = Path(__file__).resolve().parents[1]
    atoms = load_icp_atoms(root / "data/icp/compiled", root / "data/icp/raw", auto_compile=True)
    panel = build_panel(atoms, root / "configs/panels/usa_gcc_balanced.yaml")["panel"]
    brand = load_brand_context(root / "data/brand")
    rules = load_rules(root / "data/rules")
    copy = (root / "inputs/ads/sample_locad_ad_copy.txt").read_text()
    result = lint_ad_evidence(copy, panel, brand, rules)
    assert result["matched_pain_points"] or result["matched_value_props"]
    assert result["icp_evidence_refs"]
