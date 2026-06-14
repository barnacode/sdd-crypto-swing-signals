"""Ingest + indicator jobs (T020 job bodies, AC-01).

On each candle close: fetch OHLCV (with venue failover), persist it, recompute indicators
deterministically, and persist them. Idempotent (C-3). These are the callables the APScheduler
trigger invokes; scheduling itself lives in ``scheduler/__init__.py``.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from aegis.domain import Timeframe
from aegis.indicators import compute_indicators
from aegis.ingestion.ohlcv import OhlcvIngestor
from aegis.persistence.repositories.market import MarketRepository


async def ingest_candles(
    sessionmaker: async_sessionmaker[AsyncSession],
    ingestor: OhlcvIngestor,
    symbol: str,
    tf: Timeframe,
) -> int:
    candles = await ingestor.fetch(symbol, tf)
    async with sessionmaker() as session:
        await MarketRepository(session).upsert_candles(candles)
        await session.commit()
    return len(candles)


async def compute_and_store_indicators(
    sessionmaker: async_sessionmaker[AsyncSession], symbol: str, tf: Timeframe
) -> bool:
    """Recompute indicators from persisted candles; returns False if too few candles yet."""
    async with sessionmaker() as session:
        repo = MarketRepository(session)
        candles = await repo.get_candles(symbol, tf, limit=500)
        if len(candles) < 200:
            return False
        indicators = compute_indicators(candles)
        await repo.upsert_indicators(indicators)
        await session.commit()
    return True
