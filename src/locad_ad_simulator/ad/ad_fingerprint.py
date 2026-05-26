from __future__ import annotations

import hashlib
from pathlib import Path


def fingerprint_ad(copy_text: str, image_path: Path | None = None) -> str:
    h = hashlib.sha256()
    h.update(copy_text.encode("utf-8"))
    if image_path and image_path.exists():
        h.update(image_path.read_bytes())
    return h.hexdigest()[:16]
