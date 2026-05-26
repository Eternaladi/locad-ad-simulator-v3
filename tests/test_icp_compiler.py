from pathlib import Path

from locad_ad_simulator.ingest.icp_compiler import compile_icp_files
from locad_ad_simulator.ingest.icp_loader import load_icp_atoms


def test_compile_icps(tmp_path):
    root = Path(__file__).resolve().parents[1]
    out = tmp_path / "compiled"
    result = compile_icp_files(root / "data/icp/raw", out)
    assert result["total_atoms"] >= 200  # updated: 3 new market ICP files add 20 atoms
    atoms = load_icp_atoms(out, auto_compile=False)
    assert atoms[0]["icp_id"]
    assert isinstance(atoms[0]["top_pain_points"], list)
