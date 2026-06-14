"""Domain enumerations for AEGIS.

String-valued enums so they serialize cleanly across the API, persistence, and AI
structured output (the determinism boundary, C-2).
"""

from __future__ import annotations

from enum import StrEnum


class Timeframe(StrEnum):
    M15 = "15m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"


class Side(StrEnum):
    # Phase 1 / MVP is long-only spot.
    LONG = "LONG"


class EntryType(StrEnum):
    LIMIT = "LIMIT"
    MARKET = "MARKET"


class OrderStructure(StrEnum):
    OCO = "OCO"
    TP_SL = "TP_SL"
    MARKET_TRAILING = "MARKET_TRAILING"


class TimeInForce(StrEnum):
    GTC = "GTC"


class Regime(StrEnum):
    TRENDING = "trending"
    RANGING = "ranging"
    HIGH_VOL = "high_vol"


class BtcState(StrEnum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class SignalStatus(StrEnum):
    EMITTED = "EMITTED"
    ACTIVE = "ACTIVE"
    TARGET_HIT = "TARGET_HIT"
    STOPPED = "STOPPED"
    INVALIDATED = "INVALIDATED"
    EXPIRED = "EXPIRED"
    DISCARDED = "DISCARDED"


class AlertType(StrEnum):
    SIGNAL = "SIGNAL"
    TRADE_MANAGEMENT = "TRADE_MANAGEMENT"
    INVALIDATED = "INVALIDATED"
    TARGET_HIT = "TARGET_HIT"
    STOP_HIT = "STOP_HIT"
    SECURITY_ALERT = "SECURITY_ALERT"
    MACRO_EVENT = "MACRO_EVENT"
    SYSTEMIC_ALERT = "SYSTEMIC_ALERT"


class OutcomeResult(StrEnum):
    HIT = "HIT"
    STOP = "STOP"
    EXPIRED = "EXPIRED"


class StrategyStatus(StrEnum):
    SHADOW = "shadow"
    PRODUCTION = "production"
    RETIRED = "retired"


class MacroImpact(StrEnum):
    MAXIMUM = "maximum"
    MEDIUM = "medium"
