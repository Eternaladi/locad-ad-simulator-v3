from __future__ import annotations

from pathlib import Path
from locad_ad_simulator.core.types import AdInput


def load_ad(copy_path: Path | None = None, copy_text: str | None = None, image_path: Path | None = None, ad_id: str | None = None) -> AdInput:
    if copy_path:
        text = copy_path.read_text(encoding="utf-8").strip()
    elif copy_text is not None:
        text = copy_text.strip()
    else:
        raise ValueError("Either copy_path or copy_text must be provided")
    if not text:
        raise ValueError("Ad copy is empty")
    resolved_id = ad_id or (copy_path.stem.replace("_copy", "") if copy_path else "inline_ad")
    return AdInput(copy_text=text, copy_path=copy_path, image_path=image_path, ad_id=resolved_id)
