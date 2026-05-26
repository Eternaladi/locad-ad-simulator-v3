#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from locad_ad_simulator.cli import compile_icps_cli

if __name__ == "__main__":
    raise SystemExit(compile_icps_cli())
