"""Market-aware ICP loading and context for Locad Ad Simulator v2.

Given a selected market slug (usa / gcc_uae / gcc_ksa) this module:
  - Identifies which raw ICP JSON file(s) to compile and load
  - Returns market-specific gate overrides from standard.yaml
  - Provides Ramadan context flag when date falls within the Islamic holy month
  - Exposes the canonical marketplace list for that market for mismatch detection
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from locad_ad_simulator.config import load_yaml
from locad_ad_simulator.ingest.icp_compiler import compile_icp_files

# ── constants ──────────────────────────────────────────────────────────────────

VALID_MARKETS = ["usa", "gcc_uae", "gcc_ksa"]

MARKET_ICP_FILES: dict[str, str] = {
    "usa": "icp_locad_usa.json",
    "gcc_uae": "icp_locad_gcc_uae.json",
    "gcc_ksa": "icp_locad_gcc_ksa.json",
}

MARKET_LABELS: dict[str, str] = {
    "usa": "United States",
    "gcc_uae": "GCC (UAE-headquartered brands)",
    "gcc_ksa": "GCC (KSA-headquartered brands)",
}

# Canonical valid marketplaces per market — used for mismatch detection
MARKET_MARKETPLACES: dict[str, list[str]] = {
    "usa": ["amazon", "shopify", "ebay", "tiktok shop", "temu"],
    "gcc_uae": ["amazon", "amazon.ae", "shopify", "zid", "salla", "tiktok shop", "noon"],
    "gcc_ksa": ["amazon", "amazon.sa", "noon", "zid", "salla", "tiktok shop", "shopify"],
}

# Marketplaces that should trigger a mismatch warning for a given market
IRRELEVANT_MARKETPLACES: dict[str, list[str]] = {
    "usa": ["shopee", "lazada", "noon", "zid", "salla"],
    "gcc_uae": ["shopee", "lazada", "temu", "ebay"],
    "gcc_ksa": ["shopee", "lazada", "temu", "ebay"],
}

# Approximate Gregorian date ranges for Ramadan 2025 and 2026
RAMADAN_PERIODS = [
    (date(2025, 3, 1), date(2025, 3, 30)),
    (date(2026, 2, 18), date(2026, 3, 19)),
    (date(2027, 2, 7), date(2027, 3, 8)),
]


# ── helpers ────────────────────────────────────────────────────────────────────

def _is_ramadan(today: date | None = None) -> bool:
    """Return True if today falls within the approximate Ramadan period."""
    today = today or date.today()
    return any(start <= today <= end for start, end in RAMADAN_PERIODS)


def _load_market_icp_atoms(market: str, raw_dir: Path, compiled_dir: Path) -> list[dict[str, Any]]:
    """Compile only the market-specific ICP file into a temp directory and return atoms."""
    filename = MARKET_ICP_FILES[market]
    raw_file = raw_dir / filename
    if not raw_file.exists():
        raise FileNotFoundError(
            f"Market ICP file not found: {raw_file}\n"
            f"Expected at: data/icp/raw/{filename}"
        )
    # Use a market-specific sub-directory so market compilations don't clash
    market_compiled_dir = compiled_dir / f"market_{market}"
    market_compiled_dir.mkdir(parents=True, exist_ok=True)

    # Write a temp raw directory with only this market's file
    import tempfile, shutil
    with tempfile.TemporaryDirectory() as tmp:
        tmp_raw = Path(tmp)
        shutil.copy2(raw_file, tmp_raw / filename)
        result = compile_icp_files(tmp_raw, market_compiled_dir)

    atoms: list[dict[str, Any]] = []
    atoms_path = market_compiled_dir / "icp_atoms.jsonl"
    with atoms_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                atoms.append(json.loads(line))
    return atoms


def _get_market_gate_overrides(gate_config_path: Path, market: str) -> dict[str, Any]:
    """Return the per-market gate override block from standard.yaml (if present)."""
    try:
        cfg = load_yaml(gate_config_path)
        market_gates = cfg.get("market_gates", {})
        return market_gates.get(market, {})
    except Exception:
        return {}


# ── public API ─────────────────────────────────────────────────────────────────

def load_market_context(
    market: str,
    repo_root: Path,
    gate_name: str = "standard",
) -> dict[str, Any]:
    """Load the full market context for a validation run.

    Returns a dict with:
      market, market_label, atoms, icp_count,
      gate_overrides, is_ramadan, valid_marketplaces,
      irrelevant_marketplaces, proof_gaps_required
    """
    if market not in VALID_MARKETS:
        raise ValueError(
            f"Invalid market '{market}'. Must be one of: {', '.join(VALID_MARKETS)}"
        )

    raw_dir = repo_root / "data/icp/raw"
    compiled_dir = repo_root / "data/icp/compiled"
    gate_config_path = repo_root / "configs/gates" / f"{gate_name}.yaml"

    atoms = _load_market_icp_atoms(market, raw_dir, compiled_dir)
    gate_overrides = _get_market_gate_overrides(gate_config_path, market)
    ramadan = _is_ramadan()

    return {
        "market": market,
        "market_label": MARKET_LABELS[market],
        "atoms": atoms,
        "icp_count": len(atoms),
        "gate_overrides": gate_overrides,
        "is_ramadan": ramadan,
        "ramadan_relevant": market in ("gcc_uae", "gcc_ksa"),
        "valid_marketplaces": MARKET_MARKETPLACES[market],
        "irrelevant_marketplaces": IRRELEVANT_MARKETPLACES[market],
        "proof_gaps_required": gate_overrides.get("proof_gaps_required", []),
    }


def check_marketplace_relevance(ad_copy: str, market: str) -> list[str]:
    """Return list of marketplaces mentioned in the ad that are irrelevant for this market."""
    copy_lower = ad_copy.lower()
    irrelevant = IRRELEVANT_MARKETPLACES.get(market, [])
    return [mp for mp in irrelevant if mp.lower() in copy_lower]


def check_ramadan_gap(ad_copy: str, market: str) -> dict[str, Any]:
    """During Ramadan, check if ad addresses peak-season and gifting context."""
    if not _is_ramadan() or market not in ("gcc_uae", "gcc_ksa"):
        return {"active": False, "flag": False, "detail": ""}

    copy_lower = ad_copy.lower()
    ramadan_terms = ["ramadan", "eid", "iftar", "suhoor", "ramzan", "peak season", "gifting", "gift"]
    matches = [t for t in ramadan_terms if t in copy_lower]

    if not matches:
        return {
            "active": True,
            "flag": True,
            "detail": (
                "Ad runs during Ramadan period but contains no Ramadan/Eid context. "
                "GCC consumers expect peak-season awareness. Missing: Ramadan readiness, "
                "campaign SLA compliance, or gifting/GWP messaging. "
                "Flag: localization_fit gap."
            ),
        }
    return {
        "active": True,
        "flag": False,
        "detail": f"Ramadan context addressed via: {', '.join(matches)}",
    }
