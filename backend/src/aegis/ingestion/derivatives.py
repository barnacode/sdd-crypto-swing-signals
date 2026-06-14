"""Derivatives ingestion — Binance Futures public API (T045, FR-002).

Funding rate, open interest and long/short ratio feed gate G4 and context. Public endpoints, no
keys (C-6). Liquidations need Coinglass (key) — left as 0 in the MVP. The httpx client is injectable
so parsing is tested without the network.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import httpx

from aegis.domain import Derivatives

BINANCE_FAPI = "https://fapi.binance.com"


class DerivativesProvider:
    def __init__(
        self, client: httpx.AsyncClient | None = None, base_url: str = BINANCE_FAPI
    ) -> None:
        self._client = client
        self._base = base_url

    async def fetch(self, symbol: str) -> Derivatives:
        sym = symbol.replace("/", "")
        owns = self._client is None
        client = self._client or httpx.AsyncClient(base_url=self._base, timeout=10.0)
        try:
            funding = (await client.get("/fapi/v1/premiumIndex", params={"symbol": sym})).json()
            oi = (await client.get("/fapi/v1/openInterest", params={"symbol": sym})).json()
            lsr = (
                await client.get(
                    "/futures/data/globalLongShortAccountRatio",
                    params={"symbol": sym, "period": "5m", "limit": 1},
                )
            ).json()
        finally:
            if owns:
                await client.aclose()
        return Derivatives(
            symbol=symbol,
            ts=datetime.now(UTC),
            funding_rate=Decimal(str(funding["lastFundingRate"])),
            open_interest=Decimal(str(oi["openInterest"])),
            long_short_ratio=Decimal(str(lsr[0]["longShortRatio"])) if lsr else Decimal("0"),
            liquidations_24h=Decimal("0"),  # Coinglass (key) — placeholder in MVP
        )
