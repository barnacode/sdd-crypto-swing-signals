"""SQLAlchemy ORM models (T012/T013).

Mirrors data-model.md. Hypertables (ohlc, indicators, derivatives) carry the time column in
their primary key (TimescaleDB requirement); the rest are relational. Money/price columns use
Numeric so the Decimal figures round-trip exactly (C-2).
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import DateTime, Numeric, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from aegis.persistence.base import Base

_NUM = Numeric(20, 8)


class OhlcRow(Base):
    __tablename__ = "ohlc"
    symbol: Mapped[str] = mapped_column(String, primary_key=True)
    exchange: Mapped[str] = mapped_column(String, primary_key=True)
    tf: Mapped[str] = mapped_column(String, primary_key=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    open: Mapped[Decimal] = mapped_column(_NUM)
    high: Mapped[Decimal] = mapped_column(_NUM)
    low: Mapped[Decimal] = mapped_column(_NUM)
    close: Mapped[Decimal] = mapped_column(_NUM)
    volume: Mapped[Decimal] = mapped_column(_NUM)


class IndicatorRow(Base):
    __tablename__ = "indicators"
    symbol: Mapped[str] = mapped_column(String, primary_key=True)
    tf: Mapped[str] = mapped_column(String, primary_key=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    ema50: Mapped[Decimal] = mapped_column(_NUM)
    ema200: Mapped[Decimal] = mapped_column(_NUM)
    rsi14: Mapped[Decimal] = mapped_column(_NUM)
    macd: Mapped[Decimal] = mapped_column(_NUM)
    macd_sig: Mapped[Decimal] = mapped_column(_NUM)
    macd_hist: Mapped[Decimal] = mapped_column(_NUM)
    bb_upper: Mapped[Decimal] = mapped_column(_NUM)
    bb_mid: Mapped[Decimal] = mapped_column(_NUM)
    bb_lower: Mapped[Decimal] = mapped_column(_NUM)
    atr14: Mapped[Decimal] = mapped_column(_NUM)
    adx14: Mapped[Decimal] = mapped_column(_NUM)
    vol_rel: Mapped[Decimal] = mapped_column(_NUM)
    regime: Mapped[str] = mapped_column(String)


class DerivativesRow(Base):
    __tablename__ = "derivatives"
    symbol: Mapped[str] = mapped_column(String, primary_key=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    funding_rate: Mapped[Decimal] = mapped_column(_NUM)
    open_interest: Mapped[Decimal] = mapped_column(_NUM)
    long_short_ratio: Mapped[Decimal] = mapped_column(_NUM)
    liquidations_24h: Mapped[Decimal] = mapped_column(_NUM)


class SignalCandidateRow(Base):
    __tablename__ = "signal_candidates"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    symbol: Mapped[str] = mapped_column(String)
    tf: Mapped[str] = mapped_column(String)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    side: Mapped[str] = mapped_column(String)
    entry: Mapped[Decimal] = mapped_column(_NUM)
    stop: Mapped[Decimal] = mapped_column(_NUM)
    target: Mapped[Decimal] = mapped_column(_NUM)
    rr: Mapped[Decimal] = mapped_column(_NUM)
    score: Mapped[int] = mapped_column()
    features: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)


class SignalRow(Base):
    __tablename__ = "signals"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    candidate_id: Mapped[UUID] = mapped_column(Uuid)
    side: Mapped[str] = mapped_column(String)
    entry: Mapped[Decimal] = mapped_column(_NUM)
    stop: Mapped[Decimal] = mapped_column(_NUM)
    target: Mapped[Decimal] = mapped_column(_NUM)
    rr: Mapped[Decimal] = mapped_column(_NUM)
    confidence: Mapped[int] = mapped_column()
    thesis: Mapped[str] = mapped_column(String)
    bull_case: Mapped[str] = mapped_column(String)
    bear_case: Mapped[str] = mapped_column(String)
    invalidation: Mapped[str] = mapped_column(String)
    ai_rationale: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class OrderTicketRow(Base):
    __tablename__ = "order_tickets"
    signal_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    entry_type: Mapped[str] = mapped_column(String)
    entry_price: Mapped[Decimal] = mapped_column(_NUM)
    quantity: Mapped[Decimal] = mapped_column(_NUM)
    notional: Mapped[Decimal] = mapped_column(_NUM)
    order_structure: Mapped[str] = mapped_column(String)
    take_profit: Mapped[Decimal] = mapped_column(_NUM)
    sl_trigger: Mapped[Decimal] = mapped_column(_NUM)
    sl_limit: Mapped[Decimal] = mapped_column(_NUM)
    trailing: Mapped[dict[str, object] | None] = mapped_column(JSONB, nullable=True)
    exit_plan: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)
    tif: Mapped[str] = mapped_column(String)
    target_exchange: Mapped[str] = mapped_column(String)
    valid_until: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class AIAuditRow(Base):
    __tablename__ = "ai_audit"
    signal_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    prompt_hash: Mapped[str] = mapped_column(String)
    inputs: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)
    reasoning: Mapped[str] = mapped_column(String)
    model: Mapped[str] = mapped_column(String)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True))
