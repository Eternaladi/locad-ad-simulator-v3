from __future__ import annotations

import os
from typing import Any

from .client import LLMClient
from .json_repair import parse_json_object


class OpenAIJSONClient(LLMClient):
    def __init__(self, model: str = "gpt-5.5-pro", api_key: str | None = None, max_tokens: int = 1500):
        try:
            from openai import OpenAI  # type: ignore
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("Install openai to use OpenAIJSONClient") from exc
        self.client = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))
        self.model = model
        self.max_tokens = max_tokens

    def complete_json(self, prompt: str, *, image_path: str | None = None) -> dict[str, Any]:  # pragma: no cover - external API
        # This scaffold keeps image support for a future implementation.
        resp = self.client.responses.create(model=self.model, input=prompt, max_output_tokens=self.max_tokens)
        return parse_json_object(resp.output_text)
