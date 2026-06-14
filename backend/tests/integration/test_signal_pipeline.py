"""Signal-pipeline wiring tests (T040, US1 end-to-end-ish, AC-04/AC-05, C-1/C-2/C-4).

Wires candidate → AI decision → reconciliation → persist → Telegram alert, against a real
TimescaleDB and a fake sender. Emits only on a valid 'emit' decision that reconciles; an
unavailable AI (None) or a 'discard' decision yields no signal and no alert (fail-safe).
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from aegis.ai import parse_ai_decision
from aegis.domain import Side, SignalCandidate, Timeframe
from aegis.persistence.base import make_sessionmaker
from aegis.persistence.repositories.signals import SignalRepository
from aegis.scheduler.jobs.signal_run import run_signal_pipeline


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
        score=72,
    )


def _emit_decision():
    return parse_ai_decision(
        {
            "decision": "emit", "entry": "100", "stop": "96", "target": "108", "rr": "2.0",
            "confidence": 72, "thesis": "t", "bull_case": "b",
            "bear_case": "be", "invalidation": "inv",
        }
    )


class _StubOrchestrator:
    def __init__(self, decision):
        self.decision = decision

    def decide(self, candidates, context):
        return self.decision


class _RecordingSender:
    def __init__(self):
        self.calls = []

    async def send(self, *, chat_id, text, buttons=None):
        self.calls.append((chat_id, text))


async def test_emit_persists_and_alerts(db_engine):
    sm = make_sessionmaker(db_engine)
    candidate = _candidate()
    async with sm() as s:
        await SignalRepository(s).add_candidate(candidate)
        await s.commit()

    sender = _RecordingSender()
    async with sm() as s:
        signal = await run_signal_pipeline(
            candidate=candidate,
            context={"regime": "trending"},
            orchestrator=_StubOrchestrator(_emit_decision()),
            session=s,
            sender=sender,
            chat_id=123,
        )

    assert signal is not None
    assert len(sender.calls) == 1 and sender.calls[0][0] == 123
    async with sm() as s:
        assert await SignalRepository(s).get_signal(signal.id) is not None
        assert await SignalRepository(s).get_order_ticket(signal.id) is not None


async def test_unavailable_ai_emits_nothing(db_engine):
    sm = make_sessionmaker(db_engine)
    candidate = _candidate()
    async with sm() as s:
        await SignalRepository(s).add_candidate(candidate)
        await s.commit()

    sender = _RecordingSender()
    async with sm() as s:
        result = await run_signal_pipeline(
            candidate=candidate,
            context={},
            orchestrator=_StubOrchestrator(None),  # AI unavailable (AC-05)
            session=s,
            sender=sender,
            chat_id=1,
        )
    assert result is None and sender.calls == []


async def test_discard_decision_emits_nothing(db_engine):
    sm = make_sessionmaker(db_engine)
    candidate = _candidate()
    async with sm() as s:
        await SignalRepository(s).add_candidate(candidate)
        await s.commit()

    discard = parse_ai_decision(
        {
            "decision": "discard", "entry": "100", "stop": "96", "target": "108", "rr": "2.0",
            "confidence": 30, "thesis": "t", "bull_case": "b",
            "bear_case": "be", "invalidation": "inv",
        }
    )
    sender = _RecordingSender()
    async with sm() as s:
        result = await run_signal_pipeline(
            candidate=candidate,
            context={},
            orchestrator=_StubOrchestrator(discard),
            session=s,
            sender=sender,
            chat_id=1,
        )
    assert result is None and sender.calls == []
