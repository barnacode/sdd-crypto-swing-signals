"""Shared pytest fixtures (T014).

Loads the frozen, real Binance OHLCV snapshot (see fixtures/README.md) and exposes it both
as domain ``Candle`` objects and as a raw column dict, so indicator/confluence tests run on
real, traceable data (CLAUDE.md §10, C-8).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from aegis.domain import Candle, Timeframe

_FIXTURE = Path(__file__).parent / "fixtures" / "btcusdt_1h.json"


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
