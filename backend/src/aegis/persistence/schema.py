"""Schema bootstrap + TimescaleDB hypertables (T012).

Creates the relational tables, enables TimescaleDB, and promotes the time-series tables to
hypertables. A standalone helper for tests/dev; the production path uses Alembic migrations
(same DDL). Continuous aggregates (1h→4h→1d) are added by the migration.
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

import aegis.persistence.models  # noqa: F401  -- register tables on Base.metadata
from aegis.persistence.base import Base

_HYPERTABLES = ("ohlc", "indicators", "derivatives")


async def create_schema(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE"))
        await conn.run_sync(Base.metadata.create_all)
        for table in _HYPERTABLES:
            await conn.execute(
                text(f"SELECT create_hypertable('{table}', 'ts', if_not_exists => TRUE)")
            )


async def drop_schema(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
