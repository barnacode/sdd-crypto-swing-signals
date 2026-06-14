"""Contract tests for /candles and /indicators (T039 completion)."""

from __future__ import annotations

from aegis.domain import Timeframe
from aegis.persistence.base import make_sessionmaker
from aegis.persistence.repositories.market import MarketRepository
from aegis.scheduler.jobs.ingest import compute_and_store_indicators


async def test_candles_require_api_key(client):
    c, _settings, _ = client
    assert (await c.get("/api/v1/candles/BTC/USDT?tf=1h")).status_code == 401


async def test_candles_and_indicators(client, btc_1h_candles):
    c, settings, db_engine = client
    headers = {"X-API-Key": settings.api_key}
    sm = make_sessionmaker(db_engine)
    async with sm() as s:
        await MarketRepository(s).upsert_candles(btc_1h_candles)
        await s.commit()
    await compute_and_store_indicators(sm, "BTC/USDT", Timeframe.H1)

    candles = await c.get("/api/v1/candles/BTC/USDT?tf=1h", headers=headers)
    assert candles.status_code == 200 and len(candles.json()) == 300

    indicators = await c.get("/api/v1/indicators/BTC/USDT?tf=1h", headers=headers)
    assert indicators.status_code == 200 and "ema50" in indicators.json()


async def test_indicators_404_when_absent(client):
    c, settings, _ = client
    headers = {"X-API-Key": settings.api_key}
    resp = await c.get("/api/v1/indicators/ETH/USDT?tf=1h", headers=headers)
    assert resp.status_code == 404


async def test_invalid_timeframe_rejected(client):
    c, settings, _ = client
    headers = {"X-API-Key": settings.api_key}
    resp = await c.get("/api/v1/candles/BTC/USDT?tf=2h", headers=headers)
    assert resp.status_code == 422  # not a valid Timeframe enum value
