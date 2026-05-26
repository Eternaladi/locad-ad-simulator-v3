from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import Any

from .client import LLMClient
from .json_repair import parse_json_object


def _media_type(path: str) -> str:
    suffix = Path(path).suffix.lower()
    return {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}.get(suffix, "image/jpeg")


class AnthropicJSONClient(LLMClient):
    def __init__(self, model: str = "claude-opus-4-5", api_key: str | None = None, max_tokens: int = 1500):
        try:
            import anthropic  # type: ignore
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("Install anthropic to use AnthropicJSONClient") from exc
        self.client = anthropic.Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))
        self.model = model
        self.max_tokens = max_tokens

    def complete_json(self, prompt: str, *, image_path: str | None = None) -> dict[str, Any]:  # pragma: no cover - external API
        content: list[dict[str, Any]] = []
        if image_path:
            data = base64.b64encode(Path(image_path).read_bytes()).decode("utf-8")
            content.append({"type": "image", "source": {"type": "base64", "media_type": _media_type(image_path), "data": data}})
        content.append({"type": "text", "text": prompt})
        msg = self.client.messages.create(model=self.model, max_tokens=self.max_tokens, messages=[{"role": "user", "content": content}])
        raw = msg.content[0].text
        return parse_json_object(raw)
