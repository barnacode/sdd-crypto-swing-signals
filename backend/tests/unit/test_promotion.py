"""Validation gate tests (T056, US5, AC-06/AC-16, C-5/C-13).

alpha-vs-HODL = strategy return minus risk-adjusted HODL return. A strategy is promoted to
production only if it meets ALL KPIs including positive alpha; otherwise it stays in shadow mode.
The circuit breaker demotes a production strategy whose precision falls below threshold for N
signals.
"""

from __future__ import annotations

from decimal import Decimal

from aegis.validation.hodl_benchmark import alpha_vs_hodl
from aegis.validation.promotion import (
    PromotionKPIs,
    PromotionThresholds,
    should_demote,
    should_promote,
)


def _kpis(**over) -> PromotionKPIs:
    base = dict(
        precision=Decimal("0.65"),
        profit_factor=Decimal("2.0"),
        rr=Decimal("2.1"),
        calibration_error=Decimal("0.05"),
        alpha_vs_hodl=Decimal("3.0"),
    )
    base.update(over)
    return PromotionKPIs(**base)


def test_alpha_is_strategy_minus_hodl():
    assert alpha_vs_hodl(
        strategy_return_pct=Decimal("12"), hodl_return_pct=Decimal("8")
    ) == Decimal("4")


def test_strategy_passing_all_kpis_is_promoted():
    promote, reasons = should_promote(_kpis(), PromotionThresholds())
    assert promote is True and reasons == ()


def test_sub_kpi_strategy_stays_in_shadow():
    # Precision below 60% → keep in shadow mode, no live Telegram alerts (AC-06).
    promote, reasons = should_promote(_kpis(precision=Decimal("0.50")), PromotionThresholds())
    assert promote is False and any("precision" in r for r in reasons)


def test_non_positive_alpha_blocks_promotion():
    # Does not beat HODL → not promoted (AC-16, C-13).
    promote, reasons = should_promote(_kpis(alpha_vs_hodl=Decimal("-1")), PromotionThresholds())
    assert promote is False and any("alpha" in r for r in reasons)


def test_circuit_breaker_demotes_on_degraded_precision():
    # Production precision below threshold for >= N signals → demote to shadow.
    assert should_demote(recent_precision=Decimal("0.40"), signals_observed=12) is True
    assert should_demote(recent_precision=Decimal("0.70"), signals_observed=12) is False
    assert should_demote(recent_precision=Decimal("0.40"), signals_observed=5) is False  # too few
