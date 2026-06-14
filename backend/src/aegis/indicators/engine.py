"""Deterministic indicator engine (T016, AC-01).

Every figure is produced here in Python and is the single source of truth for downstream
decisions (C-2). Uses pandas-ta-classic with ``talib=False`` so the computation is pure and
portable (TA-Lib is only an optional host accelerator). Idempotent: same candles -> same
``IndicatorSet`` (C-3).
"""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

import pandas as pd
import pandas_ta_classic as ta

from aegis.domain import Candle, IndicatorSet, Regime

#: ADX at/above this marks a trending regime (research.md §B-1/B-2; tunable).
ADX_TREND = 20.0
#: ATR above this quantile of the series marks a high-volatility regime.
HIGH_VOL_QUANTILE = 0.8
#: Minimum candles required to form EMA200.
MIN_CANDLES = 200


def _dec(value: object) -> Decimal:
    return Decimal(str(round(float(value), 8)))  # type: ignore[arg-type]


def _to_frame(candles: Sequence[Candle]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "open": [float(c.open) for c in candles],
            "high": [float(c.high) for c in candles],
            "low": [float(c.low) for c in candles],
            "close": [float(c.close) for c in candles],
            "volume": [float(c.volume) for c in candles],
        },
        index=[c.ts for c in candles],
    )


def _classify_regime(adx_last: float, atr_series: pd.Series, atr_last: float) -> Regime:
    if adx_last >= ADX_TREND:
        return Regime.TRENDING
    if atr_last >= float(atr_series.quantile(HIGH_VOL_QUANTILE)):
        return Regime.HIGH_VOL
    return Regime.RANGING


def compute_indicators(candles: Sequence[Candle]) -> IndicatorSet:
    """Compute the indicator set for the last closed candle.

    Raises ``ValueError`` if there are too few candles to form EMA200 (fail-safe input guard).
    """
    if len(candles) < MIN_CANDLES:
        raise ValueError(f"need >= {MIN_CANDLES} candles, got {len(candles)}")

    df = _to_frame(candles)
    close, high, low, volume = df["close"], df["high"], df["low"], df["volume"]

    ema50 = ta.ema(close, length=50, talib=False)
    ema200 = ta.ema(close, length=200, talib=False)
    rsi14 = ta.rsi(close, length=14, talib=False)
    macd = ta.macd(close, fast=12, slow=26, signal=9, talib=False)
    bbands = ta.bbands(close, length=20, std=2.0, talib=False)
    atr14 = ta.atr(high, low, close, length=14, talib=False)
    adx = ta.adx(high, low, close, length=14, talib=False)
    vol_rel = volume / volume.rolling(20).mean()

    # macd cols: [MACD, MACDh, MACDs]; bbands cols: [BBL, BBM, BBU, ...]; adx cols: [ADX, ...]
    last = -1
    last_candle = candles[-1]
    return IndicatorSet(
        symbol=last_candle.symbol,
        tf=last_candle.tf,
        ts=last_candle.ts,
        ema50=_dec(ema50.iloc[last]),
        ema200=_dec(ema200.iloc[last]),
        rsi14=_dec(rsi14.iloc[last]),
        macd=_dec(macd.iloc[last, 0]),
        macd_hist=_dec(macd.iloc[last, 1]),
        macd_sig=_dec(macd.iloc[last, 2]),
        bb_lower=_dec(bbands.iloc[last, 0]),
        bb_mid=_dec(bbands.iloc[last, 1]),
        bb_upper=_dec(bbands.iloc[last, 2]),
        atr14=_dec(atr14.iloc[last]),
        adx14=_dec(adx.iloc[last, 0]),
        vol_rel=_dec(vol_rel.iloc[last]),
        regime=_classify_regime(
            float(adx.iloc[last, 0]), atr14, float(atr14.iloc[last])
        ),
    )
