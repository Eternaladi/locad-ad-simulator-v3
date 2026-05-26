from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class LLMMessage:
    role: str
    content: str


class LLMClient:
    """Protocol-like base for future model-backed evaluators."""

    def complete_json(self, prompt: str, *, image_path: str | None = None) -> dict[str, Any]:
        raise NotImplementedError


class OfflineLLMClient(LLMClient):
    def complete_json(self, prompt: str, *, image_path: str | None = None) -> dict[str, Any]:
        return {"provider": "offline", "note": "Use deterministic evaluators unless an API-backed client is enabled."}
