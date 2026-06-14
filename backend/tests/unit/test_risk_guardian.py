"""Risk-guardian tests (T043, US2, AC-10, FR-015).

Vetoes signals that breach the bounded-sizing rules: no free capital for the notional, the 6%
aggregate risk cap, or the correlation cap. The dual-constraint sizing itself lives in the order
ticket builder; this is the portfolio-level veto.
"""

from __future__ import annotations

from decimal import Decimal

from aegis.candidates.risk_guardian import RiskInput, evaluate_risk


def _input(**over) -> RiskInput:
    base = dict(
        notional=Decimal("800"),
        risk_pct_of_candidate=Decimal("2"),
        free_capital=Decimal("3000"),
        open_aggregate_risk_pct=Decimal("2"),
        correlated_with_open=False,
    )
    base.update(over)
    return RiskInput(**base)


def test_clean_signal_approved():
    v = evaluate_risk(_input())
    assert v.approved is True and v.reasons == ()


def test_no_free_capital_for_notional_rejected():
    v = evaluate_risk(_input(notional=Decimal("4000"), free_capital=Decimal("1000")))  # AC-10
    assert not v.approved and any("free capital" in r for r in v.reasons)


def test_aggregate_risk_cap_rejected():
    # 5% already open + 2% candidate = 7% > 6% cap.
    v = evaluate_risk(_input(open_aggregate_risk_pct=Decimal("5")))
    assert not v.approved and any("aggregate" in r for r in v.reasons)


def test_correlation_cap_rejected():
    v = evaluate_risk(_input(correlated_with_open=True))
    assert not v.approved and any("correlation" in r for r in v.reasons)
