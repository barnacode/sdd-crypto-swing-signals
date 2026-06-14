"""AEGIS domain layer: enums + Pydantic schemas shared across all modules.

These are the contract types at the deterministic boundary (C-2): Python produces and
validates every figure here before any AI or persistence layer touches it.
"""

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
from aegis.domain.models import (
    RR_MIN,
    AIAudit,
    Alert,
    Backtest,
    Candle,
    ContextSnapshot,
    Derivatives,
    IndicatorSet,
    MacroEvent,
    OrderTicket,
    Outcome,
    Position,
    Signal,
    SignalCandidate,
    Strategy,
)

__all__ = [
    "RR_MIN",
    "AIAudit",
    "Alert",
    "AlertType",
    "Backtest",
    "BtcState",
    "Candle",
    "ContextSnapshot",
    "Derivatives",
    "EntryType",
    "IndicatorSet",
    "MacroEvent",
    "MacroImpact",
    "OrderStructure",
    "OrderTicket",
    "Outcome",
    "OutcomeResult",
    "Position",
    "Regime",
    "Side",
    "Signal",
    "SignalCandidate",
    "SignalStatus",
    "Strategy",
    "StrategyStatus",
    "Timeframe",
    "TimeInForce",
]
