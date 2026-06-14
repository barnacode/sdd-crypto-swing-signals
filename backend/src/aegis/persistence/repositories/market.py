"""Market-data repository: OHLC candles + computed indicators (T018/T016 persistence).

Idempotent upserts (hypertable PKs include the time column) so re-ingesting a candle is safe
(C-3). Reads feed the confluence engine and the /candles, /indicators API.
"""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aegis.domain import Candle, Derivatives, IndicatorSet, Regime, Timeframe
from aegis.persistence.models import DerivativesRow, IndicatorRow, OhlcRow


class MarketRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def upsert_candles(self, candles: Sequence[Candle]) -> None:
        for c in candles:
            await self._s.merge(
                OhlcRow(
                    symbol=c.symbol, exchange=c.exchange, tf=c.tf.value, ts=c.ts,
                    open=c.open, high=c.high, low=c.low, close=c.close, volume=c.volume,
                )
            )

    async def get_candles(
        self, symbol: str, tf: Timeframe, *, limit: int = 500
    ) -> list[Candle]:
        stmt = (
            select(OhlcRow)
            .where(OhlcRow.symbol == symbol, OhlcRow.tf == tf.value)
            .order_by(OhlcRow.ts.asc())
            .limit(limit)
        )
        rows = (await self._s.execute(stmt)).scalars().all()
        return [
            Candle(
                symbol=r.symbol, exchange=r.exchange, tf=Timeframe(r.tf), ts=r.ts,
                open=r.open, high=r.high, low=r.low, close=r.close, volume=r.volume,
            )
            for r in rows
        ]

    async def upsert_indicators(self, ind: IndicatorSet) -> None:
        await self._s.merge(
            IndicatorRow(
                symbol=ind.symbol, tf=ind.tf.value, ts=ind.ts,
                ema50=ind.ema50, ema200=ind.ema200, rsi14=ind.rsi14,
                macd=ind.macd, macd_sig=ind.macd_sig, macd_hist=ind.macd_hist,
                bb_upper=ind.bb_upper, bb_mid=ind.bb_mid, bb_lower=ind.bb_lower,
                atr14=ind.atr14, adx14=ind.adx14, vol_rel=ind.vol_rel,
                regime=ind.regime.value,
            )
        )

    async def upsert_derivatives(self, d: Derivatives) -> None:
        await self._s.merge(
            DerivativesRow(
                symbol=d.symbol, ts=d.ts, funding_rate=d.funding_rate,
                open_interest=d.open_interest, long_short_ratio=d.long_short_ratio,
                liquidations_24h=d.liquidations_24h,
            )
        )

    async def get_latest_derivatives(self, symbol: str) -> Derivatives | None:
        stmt = (
            select(DerivativesRow)
            .where(DerivativesRow.symbol == symbol)
            .order_by(DerivativesRow.ts.desc())
            .limit(1)
        )
        r = (await self._s.execute(stmt)).scalars().first()
        if r is None:
            return None
        return Derivatives(
            symbol=r.symbol, ts=r.ts, funding_rate=r.funding_rate,
            open_interest=r.open_interest, long_short_ratio=r.long_short_ratio,
            liquidations_24h=r.liquidations_24h,
        )

    async def get_latest_indicators(self, symbol: str, tf: Timeframe) -> IndicatorSet | None:
        stmt = (
            select(IndicatorRow)
            .where(IndicatorRow.symbol == symbol, IndicatorRow.tf == tf.value)
            .order_by(IndicatorRow.ts.desc())
            .limit(1)
        )
        r = (await self._s.execute(stmt)).scalars().first()
        if r is None:
            return None
        return IndicatorSet(
            symbol=r.symbol, tf=Timeframe(r.tf), ts=r.ts,
            ema50=r.ema50, ema200=r.ema200, rsi14=r.rsi14,
            macd=r.macd, macd_sig=r.macd_sig, macd_hist=r.macd_hist,
            bb_upper=r.bb_upper, bb_mid=r.bb_mid, bb_lower=r.bb_lower,
            atr14=r.atr14, adx14=r.adx14, vol_rel=r.vol_rel, regime=Regime(r.regime),
        )
