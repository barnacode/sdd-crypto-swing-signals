"""Deterministic pre-gates G1–G5 (T048, US2, FR-005, AC-02/14/15/17, C-14/C-15).

Evaluated BEFORE confluence and BEFORE any AI call. Failing any gate produces no candidate — no
LLM is spent on an unsafe setup (fail-safe, soundness over frequency). Thresholds are tunable
(research.md §B-2). BTC/ETH are judged on their own; alts are gated by BTC's regime.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from aegis.domain import BtcState, Regime

ADX_MIN = Decimal("20")  # trending floor (G1)
LIQUIDITY_FLOOR = Decimal("5000000")  # min 24h quote volume in EUR (G3)
FUNDING_MAX = Decimal("0.001")  # |funding| per 8h band (G4)
DEPEG_MAX = Decimal("0.5")  # stablecoin deviation % from $1 (G5)


@dataclass(frozen=True)
class GateInput:
    symbol: str
    is_btc_or_eth: bool
    regime: Regime
    adx14: Decimal
    btc_state: BtcState
    quote_volume_24h: Decimal
    funding_rate: Decimal
    depeg_deviation_pct: Decimal
    systemic_incident: bool
    active_security_alert: bool


@dataclass(frozen=True)
class GateResult:
    passed: bool
    blocked_by: str | None = None
    reason: str = ""


def _blocked(by: str, reason: str) -> GateResult:
    return GateResult(passed=False, blocked_by=by, reason=reason)


def evaluate_gates(inp: GateInput) -> GateResult:
    if inp.active_security_alert:
        return _blocked("security", "active security alert on the asset (AC-02)")
    # G1 — market regime: need a trending, non-extreme-volatility regime for a breakout LONG.
    if inp.adx14 < ADX_MIN or inp.regime is Regime.HIGH_VOL:
        return _blocked("G1-regime", f"non-trending / high-vol regime (ADX {inp.adx14})")
    # G2 — BTC master gate: no altcoin LONG while BTC is bearish (1d close < EMA200).
    if not inp.is_btc_or_eth and inp.btc_state is BtcState.BEARISH:
        return _blocked("G2-btc", "BTC bearish blocks altcoin LONGs (AC-14, C-15)")
    # G3 — liquidity/spread: the pair must fill the notional without material slippage.
    if inp.quote_volume_24h < LIQUIDITY_FLOOR:
        return _blocked("G3-liquidity", "insufficient 24h liquidity (AC-15)")
    # G4 — derivatives sanity: avoid entering saturated/euphoric positioning.
    if abs(inp.funding_rate) > FUNDING_MAX:
        return _blocked("G4-derivatives", "extreme funding rate")
    # G5 — systemic safeguard: stablecoin depeg or serious exchange/chain incident.
    if inp.systemic_incident or inp.depeg_deviation_pct > DEPEG_MAX:
        return _blocked("G5-systemic", "stablecoin depeg / exchange incident (AC-17, C-14)")
    return GateResult(passed=True)
