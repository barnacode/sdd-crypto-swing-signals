"""Outcome labeler tests (T055, US5, AC-08, FR-018, C-16).

Deterministic ground truth: HIT if +target reached before stop, STOP if stop reached first,
EXPIRED otherwise. A candle touching both is conservatively labeled STOP (worst case). Computed by
code, never the AI.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from aegis.domain import Candle, OutcomeResult, Side, Signal, SignalStatus, Timeframe
from aegis.validation.outcome_labeler import label_outcome

NOW = datetime(2026, 6, 14, tzinfo=UTC)


def _signal() -> Signal:
    return Signal(
        candidate_id=uuid4(), side=Side.LONG,
        entry=Decimal("100"), stop=Decimal("96"), target=Decimal("108"), rr=Decimal("2.0"),
        confidence=70, thesis="t", bull_case="b", bear_case="be", invalidation="inv",
        ai_rationale="r", status=SignalStatus.ACTIVE, ts=NOW,
    )


def _candle(high: str, low: str, close: str, i: int) -> Candle:
    return Candle(
        symbol="BTC/USDT", exchange="binance", tf=Timeframe.H1, ts=NOW + timedelta(hours=i + 1),
        open=Decimal(close), high=Decimal(high), low=Decimal(low), close=Decimal(close),
        volume=Decimal("1"),
    )


def test_hit_when_target_reached_first():
    candles = [_candle("102", "99", "101", 0), _candle("109", "104", "108", 1)]
    out = label_outcome(_signal(), candles)
    assert out.result is OutcomeResult.HIT
    assert out.realized_pct == Decimal("8.00")  # (108-100)/100


def test_stop_when_stop_reached_first():
    candles = [_candle("101", "99", "100", 0), _candle("99", "95", "96", 1)]
    out = label_outcome(_signal(), candles)
    assert out.result is OutcomeResult.STOP
    assert out.realized_pct == Decimal("-4.00")  # (96-100)/100


def test_expired_when_neither_reached():
    candles = [_candle("103", "98", "102", 0), _candle("104", "99", "103", 1)]
    out = label_outcome(_signal(), candles)
    assert out.result is OutcomeResult.EXPIRED
    assert out.realized_pct == Decimal("3.00")  # last close 103 vs entry 100


def test_candle_touching_both_is_stop():
    candles = [_candle("109", "95", "100", 0)]  # touches stop AND target in one candle
    out = label_outcome(_signal(), candles)
    assert out.result is OutcomeResult.STOP


def test_closed_at_is_the_resolving_candle():
    candles = [_candle("102", "99", "101", 0), _candle("109", "104", "108", 1)]
    out = label_outcome(_signal(), candles)
    assert out.closed_at == NOW + timedelta(hours=2)
