"""Deterministic confluence engine (T029, FR-006/007, AC-03).

Applies the conservative multi-condition LONG confluence rules (brief §7.1) over a base
``IndicatorSet`` and surfaces a scored ``SignalCandidate`` with its levels — or ``None`` when
any rule fails or R:R < 1:2 (discarded BEFORE any AI invocation, AC-03). Every figure is
produced here in Python (C-2). Thresholds are tunable (research.md §B-1).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from aegis.domain import IndicatorSet, Side, SignalCandidate


@dataclass(frozen=True)
class ConfluenceParams:
    atr_mult: Decimal = Decimal("1.5")  # technical stop = entry - atr_mult * ATR
    target_pct: Decimal = Decimal("5")  # +5% target
    min_rr: Decimal = Decimal("2")  # R:R >= 1:2 (AC-03)
    vol_factor: Decimal = Decimal("1.5")  # trigger volume >= 1.5x MA(20)
    adx_min: Decimal = Decimal("20")  # trending regime floor
    rsi_floor: Decimal = Decimal("45")
    rsi_ceiling: Decimal = Decimal("70")


@dataclass(frozen=True)
class ConfluenceInput:
    indicators: IndicatorSet
    close: Decimal
    prev_rsi14: Decimal
    prev_macd_hist: Decimal
    htf_trend_bearish: bool
    structure_confirmed: bool
    params: ConfluenceParams = field(default_factory=ConfluenceParams)


def _all_rules_pass(inp: ConfluenceInput) -> bool:
    i, p, c = inp.indicators, inp.params, inp.close
    trend = c > i.ema50 > i.ema200 and i.adx14 >= p.adx_min and not inp.htf_trend_bearish
    momentum = p.rsi_floor <= i.rsi14 < p.rsi_ceiling and i.rsi14 > inp.prev_rsi14
    macd = i.macd > i.macd_sig and i.macd_hist > inp.prev_macd_hist
    volume = i.vol_rel >= p.vol_factor
    return bool(trend and momentum and macd and volume and inp.structure_confirmed)


def _score(rr: Decimal, inp: ConfluenceInput) -> int:
    i, p = inp.indicators, inp.params
    raw = (
        Decimal("40")
        + (rr - p.min_rr) * Decimal("10")
        + (i.vol_rel - p.vol_factor) * Decimal("20")
        + (i.adx14 - p.adx_min) * Decimal("0.5")
    )
    return int(max(Decimal("0"), min(Decimal("100"), raw)))


def evaluate_confluence(inp: ConfluenceInput) -> SignalCandidate | None:
    if not _all_rules_pass(inp):
        return None

    i, p = inp.indicators, inp.params
    entry = inp.close
    stop = entry - p.atr_mult * i.atr14
    target = (entry * (Decimal("1") + p.target_pct / Decimal("100"))).quantize(Decimal("0.01"))
    risk = entry - stop
    if risk <= 0:
        return None
    rr = ((target - entry) / risk).quantize(Decimal("0.01"))
    if rr < p.min_rr:
        # Non-compliant candidate is discarded without invoking the AI (AC-03).
        return None

    return SignalCandidate(
        symbol=i.symbol,
        tf=i.tf,
        ts=i.ts,
        side=Side.LONG,
        entry=entry,
        stop=stop,
        target=target,
        rr=rr,
        score=_score(rr, inp),
        features={
            "ema50": str(i.ema50),
            "ema200": str(i.ema200),
            "rsi14": str(i.rsi14),
            "adx14": str(i.adx14),
            "vol_rel": str(i.vol_rel),
            "atr14": str(i.atr14),
            "regime": i.regime.value,
        },
    )
