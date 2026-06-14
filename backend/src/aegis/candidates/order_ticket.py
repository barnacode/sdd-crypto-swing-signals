"""Order-ticket builder + dual-constraint sizing (T030, FR-014/FR-015, AC-09/AC-11).

Builds the executable (advisory-only) order ticket for a candidate. Sizing follows the dual
constraint ``size = min(configured notional, size risking risk_pct of capital)`` (ADR-012);
the 2% risk is the safety ceiling. Structure degrades from OCO to TP_SL on venues without
native OCO (AC-11). NOTHING is ever placed (C-1).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal
from typing import Any

from aegis.domain import EntryType, OrderStructure, OrderTicket, SignalCandidate, TimeInForce

_QTY = Decimal("0.00000001")
_MONEY = Decimal("0.01")


@dataclass(frozen=True)
class SizingParams:
    capital: Decimal = Decimal("3000")  # reference capital (within €2-5k)
    risk_pct: Decimal = Decimal("0.02")  # 2% per-trade risk ceiling
    notional_max: Decimal = Decimal("1000")  # configured notional cap
    notional_min: Decimal = Decimal("500")


def _default_exit_plan() -> dict[str, Any]:
    # TP1 +3% closes 50% -> move stop to breakeven; trail the rest toward >= +5%.
    return {
        "tp1_pct": 3,
        "tp1_close_pct": 50,
        "move_to_be": True,
        "trail_callback_pct": 1.2,
    }


def build_order_ticket(
    candidate: SignalCandidate,
    *,
    venue: str = "binance",
    venue_supports_oco: bool = True,
    sizing: SizingParams | None = None,
    horizon_hours: int = 48,
    exit_plan: dict[str, Any] | None = None,
) -> OrderTicket:
    s = sizing or SizingParams()
    entry, stop, target = candidate.entry, candidate.stop, candidate.target

    risk_per_unit = entry - stop
    risk_notional = (s.capital * s.risk_pct / risk_per_unit) * entry
    notional = min(s.notional_max, risk_notional).quantize(_MONEY)
    quantity = (notional / entry).quantize(_QTY)

    structure = OrderStructure.OCO if venue_supports_oco else OrderStructure.TP_SL

    return OrderTicket(
        signal_id=None,
        entry_type=EntryType.LIMIT,
        entry_price=entry,
        quantity=quantity,
        notional=notional,
        order_structure=structure,
        take_profit=target,
        sl_trigger=stop,
        sl_limit=stop,
        trailing=None,
        exit_plan=exit_plan or _default_exit_plan(),
        tif=TimeInForce.GTC,
        target_exchange=venue,
        valid_until=candidate.ts + timedelta(hours=horizon_hours),
    )
