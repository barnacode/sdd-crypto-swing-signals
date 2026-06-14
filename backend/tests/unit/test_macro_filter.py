"""Macro pre-event filter tests (T042, US2, AC-12, FR-008).

Window: 12h before / 2h after a scheduled event, market-wide. Maximum-impact events (FOMC/CPI/NFP)
trigger a blackout (no new LONGs); medium-impact events raise a caution flag.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from aegis.candidates.macro_filter import evaluate_macro_filter
from aegis.domain import MacroEvent, MacroImpact

NOW = datetime(2026, 6, 14, 12, 0, tzinfo=UTC)


def _event(hours_from_now: float, impact: MacroImpact) -> MacroEvent:
    return MacroEvent(
        name="FOMC", category="rates", impact=impact,
        scheduled_at=NOW + timedelta(hours=hours_from_now), source="FMP",
    )


def test_no_events_no_block():
    r = evaluate_macro_filter(NOW, [])
    assert not r.blackout and not r.caution


def test_maximum_impact_in_window_blackout():
    r = evaluate_macro_filter(NOW, [_event(6, MacroImpact.MAXIMUM)])
    assert r.blackout is True


def test_maximum_impact_just_after_event_still_blackout():
    # 1h after the event (within the 2h-after window).
    r = evaluate_macro_filter(NOW, [_event(-1, MacroImpact.MAXIMUM)])
    assert r.blackout is True


def test_maximum_impact_outside_window_no_block():
    r = evaluate_macro_filter(NOW, [_event(20, MacroImpact.MAXIMUM)])
    assert not r.blackout and not r.caution


def test_medium_impact_in_window_caution_only():
    r = evaluate_macro_filter(NOW, [_event(6, MacroImpact.MEDIUM)])
    assert r.caution is True and r.blackout is False
