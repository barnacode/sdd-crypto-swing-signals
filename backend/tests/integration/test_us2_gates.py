"""US2 gate integration in the pipeline (T044, AC-02/10/12/14/15/17, FR-005).

Each adverse condition suppresses the signal; deterministic gates/macro block BEFORE the AI is
invoked (no LLM spend); the risk-guardian vetoes after the decision. A clean setup emits.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from aegis.ai import parse_ai_decision
from aegis.candidates.gates import GateInput
from aegis.candidates.risk_guardian import RiskInput
from aegis.domain import BtcState, MacroEvent, MacroImpact, Regime, Side, SignalCandidate, Timeframe
from aegis.persistence.base import make_sessionmaker
from aegis.scheduler.jobs.signal_run import run_signal_pipeline

NOW = datetime(2026, 6, 14, 12, 0, tzinfo=UTC)


def _candidate() -> SignalCandidate:
    return SignalCandidate(
        symbol="ETH/USDT", tf=Timeframe.H1, ts=NOW, side=Side.LONG,
        entry=Decimal("100"), stop=Decimal("96"), target=Decimal("108"),
        rr=Decimal("2.0"), score=72,
    )


def _emit():
    return parse_ai_decision(
        {
            "decision": "emit", "entry": "100", "stop": "96", "target": "108", "rr": "2.0",
            "confidence": 72, "thesis": "t", "bull_case": "b", "bear_case": "be",
            "invalidation": "inv",
        }
    )


def _gate(**over) -> GateInput:
    base = dict(
        symbol="ETH/USDT", is_btc_or_eth=False, regime=Regime.TRENDING, adx14=Decimal("25"),
        btc_state=BtcState.BULLISH, quote_volume_24h=Decimal("50000000"),
        funding_rate=Decimal("0.0001"), depeg_deviation_pct=Decimal("0"),
        systemic_incident=False, active_security_alert=False,
    )
    base.update(over)
    return GateInput(**base)


def _ok_risk() -> RiskInput:
    return RiskInput(
        notional=Decimal("800"), risk_pct_of_candidate=Decimal("2"),
        free_capital=Decimal("3000"), open_aggregate_risk_pct=Decimal("2"),
        correlated_with_open=False,
    )


class _CountingOrch:
    def __init__(self, decision):
        self.decision = decision
        self.calls = 0

    def decide(self, candidates, context):
        self.calls += 1
        return self.decision


class _RecordingSender:
    def __init__(self):
        self.calls = []

    async def send(self, *, chat_id, text, buttons=None):
        self.calls.append(chat_id)


async def _run(db_engine, **kwargs):
    sm = make_sessionmaker(db_engine)
    orch = _CountingOrch(_emit())
    sender = _RecordingSender()
    async with sm() as s:
        result = await run_signal_pipeline(
            candidate=_candidate(), context={}, orchestrator=orch,
            session=s, sender=sender, chat_id=1, **kwargs,
        )
    return result, orch, sender


async def test_btc_gate_suppresses_without_ai(db_engine):
    result, orch, sender = await _run(db_engine, gate_input=_gate(btc_state=BtcState.BEARISH))
    assert result is None and orch.calls == 0 and sender.calls == []  # AI never invoked


async def test_macro_blackout_suppresses_without_ai(db_engine):
    event = MacroEvent(
        name="FOMC", category="rates", impact=MacroImpact.MAXIMUM,
        scheduled_at=NOW + timedelta(hours=6), source="FMP",
    )
    result, orch, sender = await _run(db_engine, macro_now=NOW, macro_events=[event])
    assert result is None and orch.calls == 0


async def test_risk_veto_suppresses_after_decision(db_engine):
    bad_risk = RiskInput(
        notional=Decimal("4000"), risk_pct_of_candidate=Decimal("2"),
        free_capital=Decimal("1000"), open_aggregate_risk_pct=Decimal("2"),
        correlated_with_open=False,
    )
    result, orch, sender = await _run(db_engine, gate_input=_gate(), risk_input=bad_risk)
    assert result is None and orch.calls == 1 and sender.calls == []  # AI ran, but vetoed


async def test_clean_setup_emits(db_engine):
    result, orch, sender = await _run(db_engine, gate_input=_gate(), risk_input=_ok_risk())
    assert result is not None and orch.calls == 1 and sender.calls == [1]
