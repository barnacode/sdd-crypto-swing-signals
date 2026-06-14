"""Deterministic pre-gate tests (T041, US2, AC-02/14/15/17, FR-005).

Gates run BEFORE confluence and BEFORE any AI call: failing any one produces no candidate (no LLM
spend). Each gate is exercised in isolation over controlled inputs. Thresholds per research.md §B-2.
"""

from __future__ import annotations

from decimal import Decimal

from aegis.candidates.gates import GateInput, evaluate_gates
from aegis.domain import BtcState, Regime


def _input(**over) -> GateInput:
    base = dict(
        symbol="ETH/USDT",
        is_btc_or_eth=False,
        regime=Regime.TRENDING,
        adx14=Decimal("25"),
        btc_state=BtcState.BULLISH,
        quote_volume_24h=Decimal("50000000"),
        funding_rate=Decimal("0.0001"),
        depeg_deviation_pct=Decimal("0.0"),
        systemic_incident=False,
        active_security_alert=False,
    )
    base.update(over)
    return GateInput(**base)


def test_all_gates_pass_for_clean_setup():
    result = evaluate_gates(_input())
    assert result.passed is True
    assert result.blocked_by is None


def test_g1_regime_blocks_when_not_trending():
    # ADX below the trending floor on a ranging asset → no breakout LONG.
    r = evaluate_gates(_input(regime=Regime.RANGING, adx14=Decimal("12")))
    assert not r.passed and r.blocked_by == "G1-regime"


def test_g2_btc_master_blocks_alt_long_when_btc_bearish():
    # BTC bearish (1d close < EMA200) blocks altcoin LONGs (AC-14, C-15)…
    r = evaluate_gates(_input(btc_state=BtcState.BEARISH))
    assert not r.passed and r.blocked_by == "G2-btc"


def test_g2_btc_master_allows_btc_eth_themselves():
    # …but BTC/ETH are judged on their own even when BTC is bearish.
    r = evaluate_gates(_input(is_btc_or_eth=True, symbol="BTC/USDT", btc_state=BtcState.BEARISH))
    assert r.passed


def test_g3_liquidity_blocks_thin_pair():
    r = evaluate_gates(_input(quote_volume_24h=Decimal("100000")))  # below €5M floor (AC-15)
    assert not r.passed and r.blocked_by == "G3-liquidity"


def test_g4_derivatives_blocks_extreme_funding():
    r = evaluate_gates(_input(funding_rate=Decimal("0.05")))  # |funding| > 0.10%/8h band
    assert not r.passed and r.blocked_by == "G4-derivatives"


def test_g5_systemic_blocks_on_depeg():
    r = evaluate_gates(_input(depeg_deviation_pct=Decimal("1.2")))  # > 0.5% (AC-17, C-14)
    assert not r.passed and r.blocked_by == "G5-systemic"


def test_g5_systemic_blocks_on_incident():
    r = evaluate_gates(_input(systemic_incident=True))
    assert not r.passed and r.blocked_by == "G5-systemic"


def test_security_alert_blocks_asset_long():
    # Active security alert on the asset prevents LONG emission (AC-02).
    r = evaluate_gates(_input(active_security_alert=True))
    assert not r.passed and r.blocked_by == "security"
