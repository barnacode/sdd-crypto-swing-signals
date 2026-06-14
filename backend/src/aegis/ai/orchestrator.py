"""AI orchestration client (T034, FR-009/FR-013, C-7).

Routes skills by cost (Haiku for cached context synthesis, Opus for the final decision over
already-filtered candidates) and forces schema-validated structured output. The AI decides;
Python owns every number (C-2). Fail-safe parsing is integrated: an unavailable client or an
invalid payload yields no decision (AC-05).

Determinism note: on Opus 4.8 the `temperature` parameter is removed (a request that sends it
returns 400). Reproducibility comes from the JSON-schema-constrained structured output, not a
low temperature. See contracts/ai-skills.md.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Protocol

from aegis.ai.failsafe import AISignalDecision, parse_ai_decision
from aegis.domain import SignalCandidate


@dataclass(frozen=True)
class ModelRouting:
    context_model: str = "claude-haiku-4-5"  # cheap, cached market-context synthesis
    decision_model: str = "claude-opus-4-8"  # final emit/discard/watch decision


class AIClient(Protocol):
    """Transport that returns a parsed JSON object (or None if unavailable)."""

    def complete(
        self, *, model: str, system: str, user: str, schema: dict[str, Any]
    ) -> object: ...


_CONTEXT_SYSTEM = (
    "You are AEGIS market-context. Synthesize the raw feeds into the schema. "
    "Echo numeric fields from the inputs; never invent figures."
)
_DECISION_SYSTEM = (
    "You are AEGIS signal-analyst. Decide emit/discard/watch over the already-filtered "
    "candidates. Echo entry/stop/target/rr exactly from the candidate; never invent figures."
)


class SignalOrchestrator:
    def __init__(self, client: AIClient, routing: ModelRouting | None = None) -> None:
        self._client = client
        self._routing = routing or ModelRouting()

    def synthesize_context(self, raw: dict[str, Any]) -> dict[str, Any] | None:
        """market-context synthesis on Haiku (cached upstream)."""
        result = self._client.complete(
            model=self._routing.context_model,
            system=_CONTEXT_SYSTEM,
            user=json.dumps(raw, sort_keys=True),
            schema={"type": "object"},
        )
        return result if isinstance(result, dict) else None

    def decide(
        self, candidates: Sequence[SignalCandidate], context: dict[str, Any]
    ) -> AISignalDecision | None:
        """signal-analyst decision on Opus; returns None on unavailable/invalid output (AC-05)."""
        payload = {
            "candidates": [c.model_dump(mode="json") for c in candidates],
            "context": context,
        }
        result = self._client.complete(
            model=self._routing.decision_model,
            system=_DECISION_SYSTEM,
            user=json.dumps(payload, sort_keys=True),
            schema=AISignalDecision.model_json_schema(),
        )
        return parse_ai_decision(result)
