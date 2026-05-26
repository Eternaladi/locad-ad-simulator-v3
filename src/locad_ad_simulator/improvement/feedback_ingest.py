from __future__ import annotations

from pathlib import Path


def append_feedback(path: Path, row: dict[str, str]) -> None:
    import csv
    exists = path.exists()
    fieldnames = ["run_id", "ad_id", "reviewer", "useful", "wrong", "missing_context", "notes"]
    with path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not exists or path.stat().st_size == 0:
            writer.writeheader()
        writer.writerow({k: row.get(k, "") for k in fieldnames})
