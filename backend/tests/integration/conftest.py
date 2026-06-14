"""Integration fixtures: a real TimescaleDB engine with a fresh schema per test.

Skips automatically when no database is reachable, so unit tests still run without Docker.
Point at a different instance with AEGIS_TEST_DB_DSN.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncEngine

from aegis.persistence.base import make_engine
from aegis.persistence.schema import create_schema, drop_schema

TEST_DSN = os.environ.get(
    "AEGIS_TEST_DB_DSN", "postgresql+asyncpg://aegis:aegis@127.0.0.1:5432/aegis"
)


@pytest_asyncio.fixture
async def db_engine() -> AsyncIterator[AsyncEngine]:
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
