"""Context provider tests (T045/T046/T047, FR-002/FR-008).

Parsing is tested offline with httpx.MockTransport; real fetches run when the network/keys allow.
Derivatives persistence round-trips against a real TimescaleDB.
"""

from __future__ import annotations

import os
from decimal import Decimal

import httpx
import pytest

from aegis.domain import MacroImpact
from aegis.ingestion.derivatives import DerivativesProvider
from aegis.ingestion.providers.macro import MacroCalendarProvider
from aegis.ingestion.providers.sentiment import FearGreedProvider
from aegis.persistence.base import make_sessionmaker
from aegis.persistence.repositories.market import MarketRepository


def _mock(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="https://x")


# --- derivatives (T045) ---


async def test_derivatives_parsing():
    def handler(request):
        p = request.url.path
        if "premiumIndex" in p:
            return httpx.Response(200, json={"lastFundingRate": "0.0001"})
        if "openInterest" in p:
            return httpx.Response(200, json={"openInterest": "123456.7"})
        if "globalLongShortAccountRatio" in p:
            return httpx.Response(200, json=[{"longShortRatio": "1.25"}])
        return httpx.Response(404)

    d = await DerivativesProvider(_mock(handler)).fetch("BTC/USDT")
    assert d.funding_rate == Decimal("0.0001")
    assert d.open_interest == Decimal("123456.7")
    assert d.long_short_ratio == Decimal("1.25")


async def test_derivatives_persist_round_trip(db_engine):
    def handler(request):
        p = request.url.path
        if "premiumIndex" in p:
            return httpx.Response(200, json={"lastFundingRate": "0.0002"})
        if "openInterest" in p:
            return httpx.Response(200, json={"openInterest": "999"})
        return httpx.Response(200, json=[{"longShortRatio": "1.0"}])

    d = await DerivativesProvider(_mock(handler)).fetch("BTC/USDT")
    sm = make_sessionmaker(db_engine)
    async with sm() as s:
        await MarketRepository(s).upsert_derivatives(d)
        await s.commit()
    async with sm() as s:
        got = await MarketRepository(s).get_latest_derivatives("BTC/USDT")
    assert got is not None and got.funding_rate == Decimal("0.0002")


async def test_derivatives_real_binance():
    try:
        d = await DerivativesProvider().fetch("BTC/USDT")
    except Exception:  # noqa: BLE001 -- futures API/network unavailable
        pytest.skip("Binance futures not reachable")
    assert d.open_interest > 0


# --- sentiment (T046) ---


async def test_fear_greed_parsing():
    def handler(request):
        return httpx.Response(
            200, json={"data": [{"value": "55", "value_classification": "Greed"}]}
        )

    out = await FearGreedProvider(_mock(handler)).fetch()
    assert out["fear_greed"] == 55 and out["classification"] == "Greed"


async def test_fear_greed_real():
    try:
        out = await FearGreedProvider().fetch()
    except Exception:  # noqa: BLE001
        pytest.skip("alternative.me not reachable")
    assert 0 <= out["fear_greed"] <= 100


# --- macro calendar (T047) ---


async def test_macro_calendar_parsing_and_impact_mapping():
    def handler(request):
        return httpx.Response(
            200,
            json=[
                {
                    "event": "FOMC Rate Decision",
                    "date": "2026-06-18 18:00:00",
                    "impact": "High",
                    "country": "US",
                },
                {
                    "event": "Retail Sales",
                    "date": "2026-06-16 12:30:00",
                    "impact": "Medium",
                    "country": "US",
                },
                {
                    "event": "Minor print",
                    "date": "2026-06-15 09:00:00",
                    "impact": "Low",
                    "country": "US",
                },
            ],
        )

    events = await MacroCalendarProvider("dummy-key", _mock(handler)).fetch(
        date_from="2026-06-14", date_to="2026-06-20"
    )
    assert len(events) == 2  # Low dropped
    assert events[0].impact is MacroImpact.MAXIMUM and events[0].name == "FOMC Rate Decision"
    assert events[1].impact is MacroImpact.MEDIUM


async def test_macro_calendar_real():
    key = os.environ.get("FMP_API_KEY")
    if not key:
        pytest.skip("FMP_API_KEY not set")
    try:
        events = await MacroCalendarProvider(key).fetch(
            date_from="2026-06-14", date_to="2026-06-21"
        )
    except Exception:  # noqa: BLE001
        pytest.skip("FMP not reachable")
    assert isinstance(events, list)
