"""Confluence-engine unit tests (T026, AC-03, FR-006/007).

Tests the deterministic confluence LOGIC over controlled ``IndicatorSet`` inputs: all rules
must hold to surface a candidate, and a candidate failing R:R >= 1:2 is discarded *without*
any AI involvement (AC-03). Operates on indicators, so values are constructed directly.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from aegis.candidates import ConfluenceInput, evaluate_confluence
from aegis.domain import IndicatorSet, Regime, Side, Timeframe


def _indicators(**over) -> IndicatorSet:
    base = dict(
        symbol="BTC/USDT",
        tf=Timeframe.H1,
        ts=datetime(2026, 6, 14, tzinfo=UTC),
        ema50=Decimal("100"),
        ema200=Decimal("95"),
        rsi14=Decimal("55"),
        macd=Decimal("1.2"),
        macd_sig=Decimal("1.0"),
        macd_hist=Decimal("0.2"),
        bb_upper=Decimal("105"),
        bb_mid=Decimal("101"),
        bb_lower=Decimal("97"),
        atr14=Decimal("1.0"),
        adx14=Decimal("25"),
        vol_rel=Decimal("1.8"),
        regime=Regime.TRENDING,
    )
    base.update(over)
    return IndicatorSet(**base)


def _input(**over) -> ConfluenceInput:
    base = dict(
        indicators=_indicators(),
        close=Decimal("101"),
        prev_rsi14=Decimal("50"),
        prev_macd_hist=Decimal("0.1"),
        htf_trend_bearish=False,
        structure_confirmed=True,
    )
    base.update(over)
    return ConfluenceInput(**base)


def test_happy_path_surfaces_candidate():
    c = evaluate_confluence(_input())
    assert c is not None
    assert c.side is Side.LONG
    assert c.entry == Decimal("101")
    assert c.rr >= Decimal("2")
    assert 0 <= c.score <= 100
    # Determinism: every figure is reproducible (id is per-record metadata, not a figure).
    again = evaluate_confluence(_input())
    assert again is not None
    assert again.model_dump(exclude={"id"}) == c.model_dump(exclude={"id"})


def test_low_rr_is_discarded_without_ai():
    # Wide stop (large ATR) crushes R:R below 1:2 -> no candidate (AC-03).
    c = evaluate_confluence(_input(indicators=_indicators(atr14=Decimal("3.0"))))
    assert c is None


def test_trend_gate_blocks_when_price_below_ema():
    assert evaluate_confluence(_input(close=Decimal("99"))) is None


def test_trend_gate_blocks_when_htf_bearish():
    assert evaluate_confluence(_input(htf_trend_bearish=True)) is None


def test_momentum_gate_blocks_overbought():
    assert evaluate_confluence(_input(indicators=_indicators(rsi14=Decimal("72")))) is None


def test_momentum_gate_blocks_when_not_rising():
    assert evaluate_confluence(_input(prev_rsi14=Decimal("56"))) is None


def test_macd_gate_blocks_bearish_cross():
    assert evaluate_confluence(_input(indicators=_indicators(macd=Decimal("0.9")))) is None


def test_volume_gate_blocks_thin_volume():
    assert evaluate_confluence(_input(indicators=_indicators(vol_rel=Decimal("1.0")))) is None


def test_structure_gate_blocks_unconfirmed():
    assert evaluate_confluence(_input(structure_confirmed=False)) is None
