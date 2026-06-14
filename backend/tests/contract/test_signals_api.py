"""Contract tests for the signals API (T024/T022, AC-04/AC-09, FR-023).

Exercises the /api/v1 surface against a real TimescaleDB: health is public, reads require the
API key, the AI publish path persists only figures that reconcile with the candidate (409 on
mismatch, AC-04), and there is NO order-execution endpoint (C-1, FR-023).
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from aegis.ai import build_signal_from_decision, parse_ai_decision
from aegis.api.app import create_app
from aegis.candidates import build_order_ticket
from aegis.config.settings import Settings
from aegis.domain import Side, SignalCandidate, Timeframe
from aegis.persistence.base import make_sessionmaker
from aegis.persistence.repositories.signals import SignalRepository


def _candidate() -> SignalCandidate:
    return SignalCandidate(
        symbol="BTC/USDT",
        tf=Timeframe.H1,
        ts=datetime(2026, 6, 14, tzinfo=UTC),
        side=Side.LONG,
        entry=Decimal("100"),
        stop=Decimal("96"),
        target=Decimal("108"),
        rr=Decimal("2.0"),
        score=70,
    )


def _signal_json(candidate: SignalCandidate, **over):
    decision = parse_ai_decision(
        {
            "decision": "emit",
            "entry": "100", "stop": "96", "target": "108", "rr": "2.0",
            "confidence": 70, "thesis": "t", "bull_case": "b",
            "bear_case": "be", "invalidation": "inv",
        }
    )
    assert decision is not None
    sig = build_signal_from_decision(candidate, decision).model_copy(update=over)
    return sig.model_dump(mode="json")


@pytest_asyncio.fixture
async def client(db_engine):
    settings = Settings()
    app = create_app(settings)
    app.state.sessionmaker = make_sessionmaker(db_engine)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c, settings, db_engine


async def _persist_candidate(db_engine, candidate):
    async with make_sessionmaker(db_engine)() as s:
        await SignalRepository(s).add_candidate(candidate)
        await s.commit()


async def test_health_is_public(client):
    c, _settings, _ = client
    assert (await c.get("/api/v1/health")).status_code == 200


async def test_reads_require_api_key(client):
    c, _settings, _ = client
    assert (await c.get("/api/v1/signals")).status_code == 401
    assert (await c.get("/api/v1/signals", headers={"X-API-Key": "wrong"})).status_code == 401


async def test_publish_then_list_and_fetch(client):
    c, settings, db_engine = client
    headers = {"X-API-Key": settings.api_key}
    candidate = _candidate()
    await _persist_candidate(db_engine, candidate)

    published = await c.post(
        "/api/v1/internal/signals", json=_signal_json(candidate), headers=headers
    )
    assert published.status_code == 201, published.text
    signal_id = published.json()["id"]

    listed = await c.get("/api/v1/signals", headers=headers)
    assert listed.status_code == 200
    assert any(s["id"] == signal_id for s in listed.json())

    one = await c.get(f"/api/v1/signals/{signal_id}", headers=headers)
    assert one.status_code == 200 and one.json()["rr"] == "2.00000000"


async def test_publish_rejects_reconciliation_mismatch(client):
    c, settings, db_engine = client
    headers = {"X-API-Key": settings.api_key}
    candidate = _candidate()
    await _persist_candidate(db_engine, candidate)

    # Tamper a figure: the entry no longer matches the persisted candidate (AC-04).
    tampered = _signal_json(candidate, entry=Decimal("101"))
    resp = await c.post("/api/v1/internal/signals", json=tampered, headers=headers)
    assert resp.status_code == 409, resp.text


async def test_unknown_signal_and_order_return_404(client):
    c, settings, _ = client
    headers = {"X-API-Key": settings.api_key}
    from uuid import uuid4

    missing = uuid4()
    assert (await c.get(f"/api/v1/signals/{missing}", headers=headers)).status_code == 404
    assert (await c.get(f"/api/v1/signals/{missing}/order", headers=headers)).status_code == 404


async def test_publish_unknown_candidate_returns_404(client):
    c, settings, _ = client
    headers = {"X-API-Key": settings.api_key}
    # A well-formed signal whose candidate was never persisted.
    assert (
        await c.post("/api/v1/internal/signals", json=_signal_json(_candidate()), headers=headers)
    ).status_code == 404


async def test_order_ticket_endpoint(client):
    c, settings, db_engine = client
    headers = {"X-API-Key": settings.api_key}
    candidate = _candidate()
    await _persist_candidate(db_engine, candidate)
    signal_json = _signal_json(candidate)
    signal_id = signal_json["id"]
    await c.post("/api/v1/internal/signals", json=signal_json, headers=headers)

    # Persist the order ticket directly, then read it via the API.
    async with make_sessionmaker(db_engine)() as s:
        from uuid import UUID

        await SignalRepository(s).add_order_ticket(UUID(signal_id), build_order_ticket(candidate))
        await s.commit()

    resp = await c.get(f"/api/v1/signals/{signal_id}/order", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["target_exchange"] == "binance"
