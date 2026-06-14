"""Ingestion tests (T017/T018, AC-01).

Failover logic is tested with an injected fetcher (no network). A real Binance fetch is exercised
when the network allows (skips otherwise). The ingest→persist→compute→store path runs against a
real TimescaleDB on the frozen real OHLCV fixture.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from aegis.domain import Candle, Timeframe
from aegis.ingestion.ohlcv import IngestionError, OhlcvIngestor
from aegis.persistence.base import make_sessionmaker
from aegis.persistence.repositories.market import MarketRepository
from aegis.scheduler.jobs.ingest import compute_and_store_indicators, ingest_candles


def _one_candle(venue: str) -> Candle:
    return Candle(
        symbol="BTC/USDT", exchange=venue, tf=Timeframe.H1,
        ts=datetime(2026, 6, 14, tzinfo=UTC),
        open=Decimal("1"), high=Decimal("2"), low=Decimal("1"),
        close=Decimal("2"), volume=Decimal("10"),
    )


async def test_failover_to_second_venue():
    async def fetcher(venue, symbol, tf, limit):
        if venue == "binance":
            raise RuntimeError("binance down")
        return [_one_candle(venue)]

    ingestor = OhlcvIngestor(["binance", "mexc"], fetcher=fetcher)
    candles = await ingestor.fetch("BTC/USDT", Timeframe.H1)
    assert candles[0].exchange == "mexc"


async def test_all_venues_fail_raises():
    async def fetcher(venue, symbol, tf, limit):
        raise RuntimeError("down")

    ingestor = OhlcvIngestor(["binance", "mexc"], fetcher=fetcher)
    with pytest.raises(IngestionError):
        await ingestor.fetch("BTC/USDT", Timeframe.H1)


async def test_real_binance_fetch():
    ingestor = OhlcvIngestor(["binance"])
    try:
        candles = await ingestor.fetch("BTC/USDT", Timeframe.H1, limit=5)
    except Exception:  # noqa: BLE001 -- network/exchange unavailable
        pytest.skip("Binance not reachable")
    assert len(candles) == 5
    assert candles[0].exchange == "binance" and candles[0].close > 0


async def test_ingest_persist_compute_store(db_engine, btc_1h_candles):
    sm = make_sessionmaker(db_engine)

    async def fetcher(venue, symbol, tf, limit):
        return btc_1h_candles  # the frozen real Binance fixture (300 candles)

    ingestor = OhlcvIngestor(["binance"], fetcher=fetcher)
    n = await ingest_candles(sm, ingestor, "BTC/USDT", Timeframe.H1)
    assert n == 300

    assert await compute_and_store_indicators(sm, "BTC/USDT", Timeframe.H1) is True
    async with sm() as s:
        ind = await MarketRepository(s).get_latest_indicators("BTC/USDT", Timeframe.H1)
    assert ind is not None and ind.ema50 > 0
    # Idempotent: re-ingesting the same candles does not duplicate.
    await ingest_candles(sm, ingestor, "BTC/USDT", Timeframe.H1)
    async with sm() as s:
        assert len(await MarketRepository(s).get_candles("BTC/USDT", Timeframe.H1)) == 300
