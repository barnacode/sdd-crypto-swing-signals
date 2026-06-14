"""OHLCV ingestion via ccxt async (T018, FR-001).

Public endpoints only — no keys, no fund risk (C-1/C-6). Tries venues in order and fails over on
any error (Binance → MEXC → Coinbase → BitMart). The per-venue fetcher is injectable so failover
is testable without the network.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence
from datetime import UTC, datetime
from decimal import Decimal

import ccxt.async_support as ccxt

from aegis.domain import Candle, Timeframe

DEFAULT_VENUES: tuple[str, ...] = ("binance", "mexc", "coinbase", "bitmart")

Fetcher = Callable[[str, str, Timeframe, int], Awaitable[list[Candle]]]


class IngestionError(RuntimeError):
    pass


async def _fetch_from_venue(venue: str, symbol: str, tf: Timeframe, limit: int) -> list[Candle]:
    exchange = getattr(ccxt, venue)({"enableRateLimit": True})
    try:
        raw = await exchange.fetch_ohlcv(symbol, timeframe=tf.value, limit=limit)
    finally:
        await exchange.close()
    return [
        Candle(
            symbol=symbol,
            exchange=venue,
            tf=tf,
            ts=datetime.fromtimestamp(row[0] / 1000, tz=UTC),
            open=Decimal(str(row[1])),
            high=Decimal(str(row[2])),
            low=Decimal(str(row[3])),
            close=Decimal(str(row[4])),
            volume=Decimal(str(row[5])),
        )
        for row in raw
    ]


class OhlcvIngestor:
    def __init__(
        self, venues: Sequence[str] = DEFAULT_VENUES, *, fetcher: Fetcher = _fetch_from_venue
    ) -> None:
        self._venues = tuple(venues)
        self._fetcher = fetcher

    async def fetch(self, symbol: str, tf: Timeframe, *, limit: int = 300) -> list[Candle]:
        errors: list[str] = []
        for venue in self._venues:
            try:
                return await self._fetcher(venue, symbol, tf, limit)
            except Exception as exc:  # noqa: BLE001 -- any venue error ⇒ fail over to the next
                errors.append(f"{venue}: {exc!r}")
        raise IngestionError(f"all venues failed for {symbol} {tf.value}: {errors}")
