"""Sentiment provider — Fear & Greed index (T046, FR-002/FR-003).

A SLOW regime filter, not an intraday trigger (free tier updates daily, FR-003). No key. The httpx
client is injectable for offline tests.
"""

from __future__ import annotations

import httpx

ALTERNATIVE_ME = "https://api.alternative.me"


class FearGreedProvider:
    def __init__(
        self, client: httpx.AsyncClient | None = None, base_url: str = ALTERNATIVE_ME
    ) -> None:
        self._client = client
        self._base = base_url

    async def fetch(self) -> dict[str, object]:
        owns = self._client is None
        client = self._client or httpx.AsyncClient(base_url=self._base, timeout=10.0)
        try:
            payload = (await client.get("/fng/", params={"limit": 1})).json()
        finally:
            if owns:
                await client.aclose()
        entry = payload["data"][0]
        return {
            "fear_greed": int(entry["value"]),
            "classification": entry["value_classification"],
        }
