"""Unit tests for the domain schemas (T009).

These validate the *requirements encoded in the types*: LONG geometry, R:R >= 1:2 guard
(AC-03), bounded confidence, and the signal<->candidate figure equality that the post-AI
reconciliation relies on (AC-04, C-2). Pure Pydantic — no DB/TA-Lib needed.
"""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from aegis.domain import (
    OrderStructure,
    Side,
    Signal,
    SignalCandidate,
    SignalStatus,
    Timeframe,
)


def _candidate(**overrides) -> SignalCandidate:
    base = dict(
        symbol="BTC/USDT",
        tf=Timeframe.H1,
        ts=datetime(2026, 6, 14, tzinfo=UTC),
        side=Side.LONG,
        entry=Decimal("100"),
        stop=Decimal("96"),
        target=Decimal("108"),  # +8% ; risk 4 ; reward 8 ; rr = 2.0
        rr=Decimal("2.0"),
        score=72,
        features={"adx14": "23"},
    )
    base.update(overrides)
    return SignalCandidate(**base)


def test_timeframe_values():
    assert Timeframe.H1.value == "1h"
    assert Timeframe.M15.value == "15m"


def test_valid_long_candidate():
    c = _candidate()
    assert c.side is Side.LONG
    assert c.rr == Decimal("2.0")


def test_candidate_rejects_rr_below_two():
    # AC-03: a candidate not reaching R:R >= 1:2 must not exist.
    with pytest.raises(ValidationError):
        _candidate(target=Decimal("104"), rr=Decimal("1.0"))  # reward 4 vs risk 4 -> rr 1.0


def test_candidate_rejects_inverted_levels():
    with pytest.raises(ValidationError):
        _candidate(target=Decimal("95"))  # target below entry for a LONG


def test_candidate_rr_must_match_geometry():
    # rr field must equal (target-entry)/(entry-stop) — no fabricated ratio.
    with pytest.raises(ValidationError):
        _candidate(rr=Decimal("3.0"))  # geometry says 2.0


def test_signal_confidence_bounds():
    c = _candidate()
    with pytest.raises(ValidationError):
        Signal(
            candidate_id=c.id,
            side=c.side,
            entry=c.entry,
            stop=c.stop,
            target=c.target,
            rr=c.rr,
            confidence=130,
            thesis="t",
            bull_case="b",
            bear_case="be",
            invalidation="inv",
            ai_rationale="r",
            status=SignalStatus.EMITTED,
            ts=c.ts,
        )


def test_signal_matches_candidate_reconciliation():
    # AC-04 / C-2: every figure in the signal must equal the persisted candidate.
    c = _candidate()
    ok = Signal(
        candidate_id=c.id,
        side=c.side,
        entry=c.entry,
        stop=c.stop,
        target=c.target,
        rr=c.rr,
        confidence=70,
        thesis="t",
        bull_case="b",
        bear_case="be",
        invalidation="inv",
        ai_rationale="r",
        status=SignalStatus.EMITTED,
        ts=c.ts,
    )
    assert ok.matches_candidate(c) is True

    tampered = ok.model_copy(update={"entry": Decimal("101")})
    assert tampered.matches_candidate(c) is False


def test_order_structure_enum():
    assert OrderStructure.OCO.value == "OCO"
    assert set(OrderStructure) >= {
        OrderStructure.OCO,
        OrderStructure.TP_SL,
        OrderStructure.MARKET_TRAILING,
    }
