"""Post-AI reconciliation + fail-safe tests (T027, AC-04/AC-05, C-2/FR-012).

Reconciliation: a signal/ticket whose figures differ from the persisted candidate is rejected
(AC-04). Fail-safe: an unavailable AI (None) or a schema-invalid / missing-figure output yields
no decision to emit (AC-05) — never an exception that would crash the pipeline into emitting.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from aegis.ai import (
    build_signal_from_decision,
    parse_ai_decision,
    reconcile_signal,
    should_emit,
)
from aegis.candidates import build_order_ticket
from aegis.domain import Side, SignalCandidate, Timeframe


def _candidate() -> SignalCandidate:
    return SignalCandidate(
        symbol="BTC/USDT",
        tf=Timeframe.H1,
        ts=datetime(2026, 6, 14, tzinfo=UTC),
        side=Side.LONG,
        entry=Decimal("100"),
        stop=Decimal("96"),
        target=Decimal("108"),
        rr=Decimal("2.0"),
        score=70,
    )


def _raw(**over) -> dict:
    base = dict(
        decision="emit",
        entry="100",
        stop="96",
        target="108",
        rr="2.0",
        confidence=72,
        thesis="breakout with volume",
        bull_case="trend + momentum",
        bear_case="macro risk",
        invalidation="close below 96",
    )
    base.update(over)
    return base


# --- fail-safe ---------------------------------------------------------------


def test_parse_valid_decision():
    d = parse_ai_decision(_raw())
    assert d is not None and d.decision == "emit"


def test_parse_returns_none_on_missing_figure():
    raw = _raw()
    del raw["target"]  # AI omitted a number -> fail-safe, no decision (AC-05)
    assert parse_ai_decision(raw) is None


def test_parse_returns_none_on_invalid_confidence():
    assert parse_ai_decision(_raw(confidence=130)) is None


def test_parse_returns_none_on_garbage():
    assert parse_ai_decision("not a decision") is None


def test_should_emit_only_on_emit_decision():
    assert should_emit(parse_ai_decision(_raw())) is True
    assert should_emit(parse_ai_decision(_raw(decision="discard"))) is False
    assert should_emit(None) is False  # AI unavailable (AC-05)


# --- reconciliation ----------------------------------------------------------


def test_signal_built_from_candidate_reconciles():
    c = _candidate()
    d = parse_ai_decision(_raw())
    assert d is not None
    sig = build_signal_from_decision(c, d)
    ticket = build_order_ticket(c)
    result = reconcile_signal(sig, c, ticket)
    assert result.ok is True
    assert result.reasons == ()


def test_reconciliation_rejects_tampered_signal_figure():
    c = _candidate()
    d = parse_ai_decision(_raw())
    assert d is not None
    sig = build_signal_from_decision(c, d).model_copy(update={"entry": Decimal("101")})
    result = reconcile_signal(sig, c)
    assert result.ok is False
    assert any("entry" in r for r in result.reasons)


def test_reconciliation_rejects_tampered_ticket_figure():
    c = _candidate()
    d = parse_ai_decision(_raw())
    assert d is not None
    sig = build_signal_from_decision(c, d)
    ticket = build_order_ticket(c).model_copy(update={"take_profit": Decimal("999")})
    result = reconcile_signal(sig, c, ticket)
    assert result.ok is False
    assert any("take_profit" in r for r in result.reasons)
