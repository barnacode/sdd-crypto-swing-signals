"""Async persistence base (T013).

SQLAlchemy 2.0 async engine + session factory and the declarative ``Base``. TimescaleDB is the
single store (C-2/ADR-003); repositories build on the session created here.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def make_engine(dsn: str) -> AsyncEngine:
    return create_async_engine(dsn, pool_pre_ping=True, future=True)


def make_sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)
