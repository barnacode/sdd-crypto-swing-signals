"""Persistence integration tests against a real TimescaleDB (T012/T013/T031).

Round-trips the candidate, signal, order ticket, and AI audit, and verifies that the post-AI
reconciliation holds against figures read back from the database (AC-04 end-to-end), and that
the time-series tables are real hypertables (TimescaleDB).
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import text

from aegis.ai import build_signal_from_decision, parse_ai_decision, reconcile_signal
from aegis.candidates import build_order_ticket
from aegis.domain import AIAudit, Side, SignalCandidate, Timeframe
from aegis.persistence.base import make_sessionmaker
from aegis.persistence.repositories.signals import SignalRepository


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
        features={"adx14": "25"},
    )


async def test_candidate_round_trip(db_engine):
    sm = make_sessionmaker(db_engine)
    c = _candidate()
    async with sm() as s:
        await SignalRepository(s).add_candidate(c)
        await s.commit()
    async with sm() as s:
        got = await SignalRepository(s).get_candidate(c.id)
    assert got is not None
    assert got.model_dump(exclude={"features"}) == c.model_dump(exclude={"features"})
    assert got.entry == c.entry and got.rr == c.rr


async def test_full_signal_persists_and_reconciles(db_engine):
    sm = make_sessionmaker(db_engine)
    c = _candidate()
    decision = parse_ai_decision(
        {
            "decision": "emit",
            "entry": "100",
            "stop": "96",
            "target": "108",
            "rr": "2.0",
            "confidence": 70,
            "thesis": "t",
            "bull_case": "b",
            "bear_case": "be",
            "invalidation": "inv",
        }
    )
    assert decision is not None
    signal = build_signal_from_decision(c, decision)
    ticket = build_order_ticket(c)
    audit = AIAudit(
        signal_id=signal.id,
        prompt_hash="abc123",
        inputs={"candidate_id": str(c.id)},
        reasoning="bull vs bear",
        model="claude-opus-4-8",
        ts=c.ts,
    )

    async with sm() as s:
        repo = SignalRepository(s)
        await repo.add_candidate(c)
        await repo.add_signal(signal)
        await repo.add_order_ticket(signal.id, ticket)
        await repo.add_ai_audit(audit)
        await s.commit()

    # Read everything back and reconcile against the persisted candidate (AC-04).
    async with sm() as s:
        repo = SignalRepository(s)
        db_candidate = await repo.get_candidate(c.id)
        db_signal = await repo.get_signal(signal.id)
        db_ticket = await repo.get_order_ticket(signal.id)

    assert db_candidate is not None and db_signal is not None and db_ticket is not None
    result = reconcile_signal(db_signal, db_candidate, db_ticket)
    assert result.ok is True, result.reasons


async def test_getters_return_none_when_absent(db_engine):
    from uuid import uuid4

    sm = make_sessionmaker(db_engine)
    async with sm() as s:
        repo = SignalRepository(s)
        missing = uuid4()
        assert await repo.get_candidate(missing) is None
        assert await repo.get_signal(missing) is None
        assert await repo.get_order_ticket(missing) is None


async def test_timeseries_tables_are_hypertables(db_engine):
    async with db_engine.connect() as conn:
        rows = await conn.execute(
            text("SELECT hypertable_name FROM timescaledb_information.hypertables")
        )
        names = {r[0] for r in rows}
    assert {"ohlc", "indicators", "derivatives"} <= names
