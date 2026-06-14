"""Promotion gate + circuit breaker (T063, US5, AC-06/AC-16, C-5/C-13).

A strategy stays in shadow mode (logging, no Telegram) until it meets ALL promotion KPIs including
positive alpha-vs-HODL. In production, a strategy whose precision falls below threshold for N
signals is automatically demoted back to shadow. Thresholds default to research.md §B-7.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class PromotionKPIs:
    precision: Decimal  # fraction 0–1
    profit_factor: Decimal
    rr: Decimal
    calibration_error: Decimal  # fraction 0–1
    alpha_vs_hodl: Decimal


@dataclass(frozen=True)
class PromotionThresholds:
    min_precision: Decimal = Decimal("0.60")
    min_profit_factor: Decimal = Decimal("1.8")
    min_rr: Decimal = Decimal("2.0")
    max_calibration_error: Decimal = Decimal("0.10")
    min_alpha: Decimal = Decimal("0")


@dataclass(frozen=True)
class DemotionPolicy:
    precision_floor: Decimal = Decimal("0.50")
    min_signals: int = 10  # N: observe at least this many before demoting


def should_promote(
    kpis: PromotionKPIs, thresholds: PromotionThresholds
) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    if kpis.precision < thresholds.min_precision:
        reasons.append(f"precision {kpis.precision} < {thresholds.min_precision}")
    if kpis.profit_factor < thresholds.min_profit_factor:
        reasons.append(f"profit_factor {kpis.profit_factor} < {thresholds.min_profit_factor}")
    if kpis.rr < thresholds.min_rr:
        reasons.append(f"rr {kpis.rr} < {thresholds.min_rr}")
    if kpis.calibration_error > thresholds.max_calibration_error:
        reasons.append(f"calibration {kpis.calibration_error} > {thresholds.max_calibration_error}")
    if kpis.alpha_vs_hodl <= thresholds.min_alpha:
        reasons.append(f"alpha {kpis.alpha_vs_hodl} <= {thresholds.min_alpha} (does not beat HODL)")
    return (not reasons, tuple(reasons))


def should_demote(
    *, recent_precision: Decimal, signals_observed: int, policy: DemotionPolicy | None = None
) -> bool:
    policy = policy or DemotionPolicy()
    return signals_observed >= policy.min_signals and recent_precision < policy.precision_floor
