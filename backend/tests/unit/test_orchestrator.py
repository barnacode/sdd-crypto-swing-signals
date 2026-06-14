"""AI orchestration unit tests (T034, FR-009/FR-013).

Tests the orchestration LOGIC with a stub AIClient — no network, no API key. Verifies model
routing (Haiku for context, Opus for the decision) and that fail-safe parsing is integrated:
an unavailable client (None) or a schema-invalid payload yields no decision (AC-05).
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from aegis.ai import SignalOrchestrator
from aegis.ai.orchestrator import ModelRouting
from aegis.domain import Side, SignalCandidate, Timeframe


class StubAIClient:
    """Records the model used and returns a canned payload (or None)."""

    def __init__(self, payload: object) -> None:
        self.payload = payload
        self.models_used: list[str] = []

    def complete(self, *, model: str, system: str, user: str, schema: dict) -> object:
        self.models_used.append(model)
        return self.payload


def _candidate() -> SignalCandidate:
    return SignalCandidate(
        symbol="BTC/USDT",
        tf=Timeframe.H1,
        ts=datetime(2026, 6, 14, tzinfo=UTC),
        side=Side.LONG,
        entry=Decimal("100"),
        stop=Decimal("96"),
        target=Decimal("108"),
        rr=Decimal("2.0"),
        score=70,
    )


def _decision_payload(**over) -> dict:
    base = dict(
        decision="emit",
        entry="100",
        stop="96",
        target="108",
        rr="2.0",
        confidence=72,
        thesis="breakout",
        bull_case="trend",
        bear_case="macro",
        invalidation="below 96",
    )
    base.update(over)
    return base


def test_decide_routes_to_opus_and_parses():
    stub = StubAIClient(_decision_payload())
    orch = SignalOrchestrator(stub, routing=ModelRouting())
    decision = orch.decide([_candidate()], context={"regime": "trending"})
    assert decision is not None and decision.decision == "emit"
    assert stub.models_used == ["claude-opus-4-8"]


def test_context_routes_to_haiku():
    stub = StubAIClient({"regime": "trending", "summary": "ok"})
    orch = SignalOrchestrator(stub)
    orch.synthesize_context({"fear_greed": 55})
    assert stub.models_used == ["claude-haiku-4-5"]


def test_decide_failsafe_on_invalid_payload():
    # Schema-invalid AI output -> no decision (AC-05, fail-safe via parse_ai_decision).
    stub = StubAIClient(_decision_payload(confidence=999))
    orch = SignalOrchestrator(stub)
    assert orch.decide([_candidate()], context={}) is None


def test_decide_failsafe_on_unavailable_client():
    # Client returns None (AI unavailable) -> no decision (AC-05).
    orch = SignalOrchestrator(StubAIClient(None))
    assert orch.decide([_candidate()], context={}) is None
