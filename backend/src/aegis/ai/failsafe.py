"""Fail-safe guard over AI output (T036, AC-05, FR-012, C-4).

The AI's structured decision is validated against a schema. If the AI is unavailable (``None``)
or its output is schema-invalid or missing a figure, we return ``None`` — there is no decision to
emit. Silence beats a bad signal (C-4); this never raises into the emit path.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError


class AISignalDecision(BaseModel):
    """signal-analyst structured output (contracts/ai-skills.md §2)."""

    model_config = ConfigDict(extra="forbid")

    decision: Literal["emit", "discard", "watch"]
    # Numeric echoes — reconciled against the candidate (the AI must not invent figures, C-2).
    entry: Decimal
    stop: Decimal
    target: Decimal
    rr: Decimal
    confidence: int = Field(ge=0, le=100)
    thesis: str
    bull_case: str
    bear_case: str
    invalidation: str


def parse_ai_decision(raw: object) -> AISignalDecision | None:
    """Validate raw AI output; return ``None`` on any invalidity (fail-safe)."""
    try:
        return AISignalDecision.model_validate(raw)
    except ValidationError:
        return None


def should_emit(decision: AISignalDecision | None) -> bool:
    return decision is not None and decision.decision == "emit"
