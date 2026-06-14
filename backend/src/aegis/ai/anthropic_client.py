"""Concrete AIClient backed by the Anthropic Messages API (T034).

Forces schema-constrained structured output via ``output_config.format`` — this, not a low
temperature, is what makes the decision reproducible (C-2/C-3). On Opus 4.8 the ``temperature``
parameter is removed and would return 400, so it is never sent. Any API error maps to ``None``
so the caller fails safe (C-4, AC-05).
"""

from __future__ import annotations

import json
from typing import Any

import anthropic


class AnthropicAIClient:
    def __init__(self, client: anthropic.Anthropic, *, max_tokens: int = 4096) -> None:
        self._client = client
        self._max_tokens = max_tokens

    def complete(
        self, *, model: str, system: str, user: str, schema: dict[str, Any]
    ) -> object:
        try:
            response = self._client.messages.create(
                model=model,
                max_tokens=self._max_tokens,
                system=system,
                messages=[{"role": "user", "content": user}],
                output_config={"format": {"type": "json_schema", "schema": schema}},
            )
        except anthropic.APIError:
            return None  # AI unavailable -> fail-safe (C-4)

        for block in response.content:
            if block.type == "text":
                data: object = json.loads(block.text)
                return data
        return None
