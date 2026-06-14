"""Domain models for AEGIS (Pydantic v2).

Money/price fields use ``Decimal`` to keep figures exact — the determinism boundary
(C-2) requires that every number be reproducible, never a float artifact. The signal's
figures must equal the candidate's exactly; ``Signal.matches_candidate`` is the basis of
the post-AI reconciliation check (AC-04).
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Self
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from aegis.domain.enums import (
    AlertType,
    BtcState,
    EntryType,
    MacroImpact,
    OrderStructure,
    OutcomeResult,
    Regime,
    Side,
    SignalStatus,
    StrategyStatus,
    Timeframe,
    TimeInForce,
)

#: Minimum risk:reward enforced at the domain boundary (AC-03, FR-007).
RR_MIN = Decimal("2")
#: Tolerance for the R:R-vs-geometry consistency check.
_RR_TOL = Decimal("0.01")


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- Market data ---------------------------------------------------------------


class Candle(_Model):
    symbol: str
    exchange: str
    tf: Timeframe
    ts: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal


class IndicatorSet(_Model):
    symbol: str
    tf: Timeframe
    ts: datetime
    ema50: Decimal
    ema200: Decimal
    rsi14: Decimal
    macd: Decimal
    macd_sig: Decimal
    macd_hist: Decimal
    bb_upper: Decimal
    bb_mid: Decimal
    bb_lower: Decimal
    atr14: Decimal
    adx14: Decimal
    vol_rel: Decimal
    regime: Regime


class Derivatives(_Model):
    symbol: str
    ts: datetime
    funding_rate: Decimal
    open_interest: Decimal
    long_short_ratio: Decimal
    liquidations_24h: Decimal


class MacroEvent(_Model):
    id: UUID = Field(default_factory=uuid4)
    name: str
    category: str
    impact: MacroImpact
    scheduled_at: datetime
    consensus: Decimal | None = None
    prior: Decimal | None = None
    actual: Decimal | None = None
    source: str


class ContextSnapshot(_Model):
    ts: datetime
    fear_greed: int
    social_score: Decimal | None = None
    news: list[dict[str, Any]] = Field(default_factory=list)
    geo_risk: Decimal
    btc_dominance: Decimal
    btc_state: BtcState
    security_flags: list[dict[str, Any]] = Field(default_factory=list)
    systemic_flags: list[dict[str, Any]] = Field(default_factory=list)
    macro_blackout: bool = False
    global_pause: bool = False


# --- Signal pipeline -----------------------------------------------------------


class SignalCandidate(_Model):
    id: UUID = Field(default_factory=uuid4)
    symbol: str
    tf: Timeframe
    ts: datetime
    side: Side
    entry: Decimal
    stop: Decimal
    target: Decimal
    rr: Decimal
    score: int = Field(ge=0, le=100)
    features: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _check_geometry_and_rr(self) -> Self:
        # LONG geometry: stop < entry < target.
        if not (self.stop < self.entry < self.target):
            raise ValueError("LONG candidate requires stop < entry < target")
        risk = self.entry - self.stop
        reward = self.target - self.entry
        if risk <= 0:
            raise ValueError("risk (entry - stop) must be positive")
        computed = (reward / risk).quantize(Decimal("0.01"))
        if abs(self.rr - computed) > _RR_TOL:
            raise ValueError(f"rr {self.rr} does not match geometry {computed}")
        if self.rr < RR_MIN:
            raise ValueError(f"R:R {self.rr} below minimum {RR_MIN} (AC-03)")
        return self


class OrderTicket(_Model):
    signal_id: UUID | None = None
    entry_type: EntryType
    entry_price: Decimal
    quantity: Decimal
    notional: Decimal
    order_structure: OrderStructure
    take_profit: Decimal
    sl_trigger: Decimal
    sl_limit: Decimal
    trailing: dict[str, Any] | None = None
    exit_plan: dict[str, Any] = Field(default_factory=dict)
    tif: TimeInForce = TimeInForce.GTC
    target_exchange: str
    valid_until: datetime


class Signal(_Model):
    id: UUID = Field(default_factory=uuid4)
    candidate_id: UUID
    side: Side
    entry: Decimal
    stop: Decimal
    target: Decimal
    rr: Decimal
    confidence: int = Field(ge=0, le=100)
    thesis: str
    bull_case: str
    bear_case: str
    invalidation: str
    ai_rationale: str
    status: SignalStatus
    ts: datetime

    def matches_candidate(self, candidate: SignalCandidate) -> bool:
        """Every figure must equal the persisted candidate (AC-04, C-2)."""
        return (
            self.candidate_id == candidate.id
            and self.side == candidate.side
            and self.entry == candidate.entry
            and self.stop == candidate.stop
            and self.target == candidate.target
            and self.rr == candidate.rr
        )


class AIAudit(_Model):
    signal_id: UUID
    prompt_hash: str
    inputs: dict[str, Any]
    reasoning: str
    model: str
    ts: datetime


class Alert(_Model):
    id: UUID = Field(default_factory=uuid4)
    signal_id: UUID | None = None
    type: AlertType
    channel: str = "telegram"
    payload: dict[str, Any] = Field(default_factory=dict)
    sent_at: datetime


class Outcome(_Model):
    signal_id: UUID
    result: OutcomeResult
    realized_pct: Decimal
    closed_at: datetime


class Position(_Model):
    id: UUID = Field(default_factory=uuid4)
    signal_id: UUID
    taken: bool
    entry_fill: Decimal | None = None
    qty: Decimal | None = None
    partials: list[dict[str, Any]] = Field(default_factory=list)
    stop_current: Decimal | None = None
    status: str = "open"
    realized_pnl: Decimal | None = None
    source: str = "manual"


class Strategy(_Model):
    id: UUID = Field(default_factory=uuid4)
    name: str
    params: dict[str, Any] = Field(default_factory=dict)
    status: StrategyStatus = StrategyStatus.SHADOW
    kpis: dict[str, Any] = Field(default_factory=dict)


class Backtest(_Model):
    id: UUID = Field(default_factory=uuid4)
    strategy: str
    params: dict[str, Any] = Field(default_factory=dict)
    metrics: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
