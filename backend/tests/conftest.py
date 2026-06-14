"""Shared pytest fixtures (T014).

Loads the frozen, real Binance OHLCV snapshot (see fixtures/README.md) and exposes it both
as domain ``Candle`` objects and as a raw column dict, so indicator/confluence tests run on
real, traceable data (CLAUDE.md §10, C-8).
"""

from __future__ import annotations

import json
import os
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncEngine

from aegis.domain import Candle, Timeframe
from aegis.persistence.base import make_engine
from aegis.persistence.schema import create_schema, drop_schema

_FIXTURE = Path(__file__).parent / "fixtures" / "btcusdt_1h.json"

TEST_DSN = os.environ.get(
    "AEGIS_TEST_DB_DSN", "postgresql+asyncpg://aegis:aegis@127.0.0.1:5432/aegis"
)


@pytest_asyncio.fixture
async def db_engine() -> AsyncIterator[AsyncEngine]:
    """A real TimescaleDB engine with a fresh schema per test; auto-skips if no DB is reachable."""
    engine = make_engine(TEST_DSN)
    try:
        await create_schema(engine)
    except Exception:  # noqa: BLE001 -- any connection/DDL failure ⇒ no DB available
        await engine.dispose()
        pytest.skip("TimescaleDB not available (set AEGIS_TEST_DB_DSN or start the container)")
    try:
        yield engine
    finally:
        await drop_schema(engine)
        await engine.dispose()


@pytest.fixture(scope="session")
def btc_1h_candles() -> list[Candle]:
    rows = json.loads(_FIXTURE.read_text())
    return [
        Candle(
            symbol="BTC/USDT",
            exchange="binance",
            tf=Timeframe.H1,
            ts=datetime.fromtimestamp(row[0] / 1000, tz=UTC),
            open=Decimal(row[1]),
            high=Decimal(row[2]),
            low=Decimal(row[3]),
            close=Decimal(row[4]),
            volume=Decimal(row[5]),
        )
        for row in rows
    ]
