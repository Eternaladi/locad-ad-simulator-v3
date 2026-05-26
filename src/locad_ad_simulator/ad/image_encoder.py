from __future__ import annotations

import base64
from pathlib import Path


def image_media_type(path: Path) -> str:
    return {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp", ".gif": "image/gif"}.get(path.suffix.lower(), "image/jpeg")


def encode_image_base64(path: Path) -> tuple[str, str]:
    return base64.b64encode(path.read_bytes()).decode("utf-8"), image_media_type(path)
