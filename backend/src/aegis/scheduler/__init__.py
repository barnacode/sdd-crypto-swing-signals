"""APScheduler wiring (T020).

Registers the 24/7 ingest+indicator jobs on each base-timeframe candle close. Built but not
started here; the runtime process calls ``.start()``. Jobs are async and run on the AsyncIO loop
(same loop as ccxt/FastAPI). The jobstore is in-memory by default and Postgres-backed in
deployment (ADR-010) — passed in by the caller.
"""

from __future__ import annotations

from collections.abc import Sequence

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from aegis.domain import Timeframe
from aegis.ingestion.ohlcv import OhlcvIngestor
from aegis.scheduler.jobs.ingest import compute_and_store_indicators, ingest_candles


async def ingest_and_compute(
    sessionmaker: async_sessionmaker[AsyncSession],
    ingestor: OhlcvIngestor,
    symbol: str,
    tf: Timeframe,
) -> None:
    await ingest_candles(sessionmaker, ingestor, symbol, tf)
    await compute_and_store_indicators(sessionmaker, symbol, tf)


def build_scheduler(
    sessionmaker: async_sessionmaker[AsyncSession],
    ingestor: OhlcvIngestor,
    *,
    symbols: Sequence[str],
    base_tf: Timeframe = Timeframe.H1,
) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    for symbol in symbols:
        scheduler.add_job(
            ingest_and_compute,
            CronTrigger(minute=0),  # on each 1h candle close
            args=[sessionmaker, ingestor, symbol, base_tf],
            id=f"ingest:{symbol}:{base_tf.value}",
            replace_existing=True,
        )
    return scheduler
