"""Risk-guardian portfolio veto (T051, US2, FR-015, AC-10, C-12).

Vetoes a sized candidate that breaches portfolio limits: no free capital for the notional, the 6%
aggregate risk cap, or the correlation cap. The dual-constraint per-trade sizing is computed by the
order ticket builder; this is the aggregate, portfolio-level check. Thresholds tunable (B-3).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

AGGREGATE_RISK_CAP = Decimal("6")  # max aggregate open risk, % of capital


@dataclass(frozen=True)
class RiskInput:
    notional: Decimal
    risk_pct_of_candidate: Decimal
    free_capital: Decimal
    open_aggregate_risk_pct: Decimal
    correlated_with_open: bool


@dataclass(frozen=True)
class RiskVerdict:
    approved: bool
    reasons: tuple[str, ...]


def evaluate_risk(inp: RiskInput) -> RiskVerdict:
    reasons: list[str] = []
    if inp.notional > inp.free_capital:
        reasons.append("no free capital for the notional")  # AC-10
    if inp.open_aggregate_risk_pct + inp.risk_pct_of_candidate > AGGREGATE_RISK_CAP:
        reasons.append(f"aggregate risk exceeds {AGGREGATE_RISK_CAP}% cap")
    if inp.correlated_with_open:
        reasons.append("correlation cap: highly correlated with an open position")
    return RiskVerdict(approved=not reasons, reasons=tuple(reasons))
