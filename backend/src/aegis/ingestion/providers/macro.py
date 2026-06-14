"""Macro economic-calendar provider — FMP (T047, FR-008, AC-12/AC-13).

Forward calendar of scheduled events that can turn the market. FMP impact strings map to AEGIS
impact (High → maximum, Medium → medium); Low and unknown are dropped. Requires FMP_API_KEY; the
parser is tested offline with an injected client.
"""

from __future__ import annotations

from datetime import UTC, datetime

import httpx

from aegis.domain import MacroEvent, MacroImpact

FMP_BASE = "https://financialmodelingprep.com"

_IMPACT = {"High": MacroImpact.MAXIMUM, "Medium": MacroImpact.MEDIUM}


def _parse_dt(raw: str) -> datetime:
    return datetime.fromisoformat(raw.replace(" ", "T")).replace(tzinfo=UTC)


class MacroCalendarProvider:
    def __init__(
        self, api_key: str, client: httpx.AsyncClient | None = None, base_url: str = FMP_BASE
    ) -> None:
        self._api_key = api_key
        self._client = client
        self._base = base_url

    async def fetch(self, *, date_from: str, date_to: str) -> list[MacroEvent]:
        owns = self._client is None
        client = self._client or httpx.AsyncClient(base_url=self._base, timeout=10.0)
        try:
            rows = (
                await client.get(
                    "/api/v3/economic_calendar",
                    params={"from": date_from, "to": date_to, "apikey": self._api_key},
                )
            ).json()
        finally:
            if owns:
                await client.aclose()

        events: list[MacroEvent] = []
        for row in rows:
            impact = _IMPACT.get(row.get("impact", ""))
            if impact is None:  # drop Low / unknown impact
                continue
            events.append(
                MacroEvent(
                    name=row["event"],
                    category=row.get("country", "macro"),
                    impact=impact,
                    scheduled_at=_parse_dt(row["date"]),
                    source="FMP",
                )
            )
        return events
