"""Deterministic outcome labeler (T058, US5, AC-08, FR-018, C-16).

Ground truth for every signal — computed by code, never the AI (anti-overfit, §13.2). Walks the
candles after entry: STOP if the stop is reached, HIT if the target is reached, EXPIRED at the end
of the horizon. A candle that touches both the stop and the target is conservatively a STOP.
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

from aegis.domain import Candle, Outcome, OutcomeResult, Signal

_PCT = Decimal("0.01")


def _pct(price: Decimal, entry: Decimal) -> Decimal:
    return ((price - entry) / entry * Decimal("100")).quantize(_PCT)


def label_outcome(signal: Signal, candles: Sequence[Candle]) -> Outcome:
    entry = signal.entry
    for candle in candles:
        if candle.low <= signal.stop:  # conservative: stop checked before target
            return Outcome(
                signal_id=signal.id,
                result=OutcomeResult.STOP,
                realized_pct=_pct(signal.stop, entry),
                closed_at=candle.ts,
            )
        if candle.high >= signal.target:
            return Outcome(
                signal_id=signal.id,
                result=OutcomeResult.HIT,
                realized_pct=_pct(signal.target, entry),
                closed_at=candle.ts,
            )
    last = candles[-1]
    return Outcome(
        signal_id=signal.id,
        result=OutcomeResult.EXPIRED,
        realized_pct=_pct(last.close, entry),
        closed_at=last.ts,
    )
