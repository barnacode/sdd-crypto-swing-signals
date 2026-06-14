"""Order-ticket + sizing unit tests (T030, AC-09/AC-11, FR-014/FR-015).

The ticket figures must reconcile with the candidate (entry/TP/SL), sizing follows the dual
constraint min(configured notional, 2%-risk size), and the structure degrades to TP_SL when
the venue lacks native OCO (AC-11). No order is ever placed (C-1).
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from aegis.candidates import SizingParams, build_order_ticket
from aegis.domain import EntryType, OrderStructure, Side, SignalCandidate, Timeframe


def _candidate(entry="100", stop="96", target="108", rr="2.0") -> SignalCandidate:
    return SignalCandidate(
        symbol="BTC/USDT",
        tf=Timeframe.H1,
        ts=datetime(2026, 6, 14, tzinfo=UTC),
        side=Side.LONG,
        entry=Decimal(entry),
        stop=Decimal(stop),
        target=Decimal(target),
        rr=Decimal(rr),
        score=70,
    )


def test_ticket_reconciles_with_candidate():
    c = _candidate()
    t = build_order_ticket(c)
    assert t.entry_type is EntryType.LIMIT
    assert t.entry_price == c.entry
    assert t.take_profit == c.target
    assert t.sl_trigger == c.stop
    assert t.target_exchange == "binance"
    assert t.valid_until > c.ts


def test_notional_capped_by_configured_max():
    # Tight stop -> 2%-risk size is huge -> configured notional max dominates (FR-015).
    c = _candidate(entry="100", stop="96", target="108", rr="2.0")
    t = build_order_ticket(c, sizing=SizingParams(capital=Decimal("3000")))
    assert t.notional == Decimal("1000.00")
    assert t.quantity == (Decimal("1000.00") / Decimal("100")).quantize(Decimal("0.00000001"))


def test_risk_ceiling_dominates_with_wide_stop():
    # Wide stop -> the 2% risk ceiling produces a smaller notional than the configured max.
    c = _candidate(entry="100", stop="90", target="130", rr="3.0")
    t = build_order_ticket(c, sizing=SizingParams(capital=Decimal("3000")))
    # risk_amount = 60 ; risk_per_unit = 10 ; qty = 6 ; notional = 600
    assert t.notional == Decimal("600.00")


def test_oco_when_supported_tp_sl_when_not():
    c = _candidate()
    assert build_order_ticket(c, venue_supports_oco=True).order_structure is OrderStructure.OCO
    assert (
        build_order_ticket(c, venue_supports_oco=False).order_structure is OrderStructure.TP_SL
    )


def test_exit_plan_present():
    t = build_order_ticket(_candidate())
    assert t.exit_plan["tp1_pct"] == 3
    assert t.exit_plan["move_to_be"] is True
