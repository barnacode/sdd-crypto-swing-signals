"""Risk-adjusted alpha-vs-HODL benchmark (T061, US5, AC-16, C-13).

The honesty metric: a strategy that does not beat buy-and-hold of BTC/ETH (risk-adjusted) over the
same period adds nothing. Here ``hodl_return_pct`` is expected to already be risk-adjusted by the
caller (Sharpe/Sortino-scaled); alpha is the excess. A full Sharpe/Sortino computation is a
follow-up; this keeps the gate (alpha > 0) explicit and testable.
"""

from __future__ import annotations

from decimal import Decimal


def alpha_vs_hodl(*, strategy_return_pct: Decimal, hodl_return_pct: Decimal) -> Decimal:
    return strategy_return_pct - hodl_return_pct
