from pathlib import Path

from locad_ad_simulator.ingest.icp_loader import load_icp_atoms
from locad_ad_simulator.panels.panel_builder import build_panel


def test_panel_builder_has_coverage():
    root = Path(__file__).resolve().parents[1]
    atoms = load_icp_atoms(root / "data/icp/compiled", root / "data/icp/raw", auto_compile=True)
    bundle = build_panel(atoms, root / "configs/panels/usa_gcc_balanced.yaml")
    assert len(bundle["panel"]) == 24
    assert bundle["coverage"]["coverage_score"] > 0
    assert "region" in bundle["coverage"]["axes"]
