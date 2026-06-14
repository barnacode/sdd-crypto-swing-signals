"""Indicator-engine unit tests (T015) on real Binance OHLCV (AC-01, C-2/C-3).

Exactness is anchored against an INDEPENDENT EMA computation (pandas `ewm`), so the test does
not just re-run the engine's own library. Other indicators are checked via mathematical
invariants. Determinism (same input -> same output) covers C-3 reproducibility.
"""

from __future__ import annotations

from decimal import Decimal

import pandas as pd
import pytest

from aegis.domain import IndicatorSet, Regime, Timeframe
from aegis.indicators import compute_indicators
from aegis.indicators.engine import _classify_regime


def test_compute_returns_full_indicator_set(btc_1h_candles):
    ind = compute_indicators(btc_1h_candles)
    assert isinstance(ind, IndicatorSet)
    assert ind.symbol == "BTC/USDT"
    assert ind.tf is Timeframe.H1
    # Computed for the last closed candle.
    assert ind.ts == btc_1h_candles[-1].ts


def test_indicator_invariants(btc_1h_candles):
    ind = compute_indicators(btc_1h_candles)
    assert Decimal("0") <= ind.rsi14 <= Decimal("100")
    assert Decimal("0") <= ind.adx14 <= Decimal("100")
    assert ind.atr14 > 0
    assert ind.ema50 > 0
    assert ind.ema200 > 0
    assert ind.bb_lower < ind.bb_mid < ind.bb_upper
    assert ind.vol_rel > 0


def test_ema50_matches_independent_computation(btc_1h_candles):
    # Independent EMA (pandas ewm, adjust=False) — different code path than the engine.
    close = pd.Series([float(c.close) for c in btc_1h_candles])
    expected = close.ewm(span=50, adjust=False).mean().iloc[-1]
    ind = compute_indicators(btc_1h_candles)
    assert abs(float(ind.ema50) - expected) / expected < 0.005  # within 0.5%


def test_engine_is_deterministic(btc_1h_candles):
    a = compute_indicators(btc_1h_candles)
    b = compute_indicators(btc_1h_candles)
    assert a == b  # same input -> identical output (C-3)


def test_regime_is_classified(btc_1h_candles):
    ind = compute_indicators(btc_1h_candles)
    assert ind.regime in set(Regime)


def test_too_few_candles_raises(btc_1h_candles):
    # Fail-safe input guard: cannot form EMA200 with too few candles.
    with pytest.raises(ValueError, match="need >="):
        compute_indicators(btc_1h_candles[:50])


def test_classify_regime_branches():
    atr = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
    # ADX >= 20 -> trending (regardless of ATR).
    assert _classify_regime(25.0, atr, 1.0) is Regime.TRENDING
    # ADX < 20 and ATR at the top -> high volatility.
    assert _classify_regime(10.0, atr, 5.0) is Regime.HIGH_VOL
    # ADX < 20 and ATR low -> ranging.
    assert _classify_regime(10.0, atr, 1.0) is Regime.RANGING
