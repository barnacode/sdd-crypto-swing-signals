"""Macro pre-event filter (T049, US2, FR-008, AC-12).

Deterministic, market-wide. Within the window (12h before / 2h after) a maximum-impact event
(rate decision, CPI, NFP) triggers a blackout — no new LONGs; a medium-impact event raises a
caution flag (reinforced confluence + reduced size, applied upstream). Tunable (research.md §B-5).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta

from aegis.domain import MacroEvent, MacroImpact

WINDOW_BEFORE = timedelta(hours=12)
WINDOW_AFTER = timedelta(hours=2)


@dataclass(frozen=True)
class MacroFilterResult:
    blackout: bool
    caution: bool
    reason: str = ""


def evaluate_macro_filter(now: datetime, events: Sequence[MacroEvent]) -> MacroFilterResult:
    caution = False
    for event in events:
        # now is in window iff scheduled - 12h <= now <= scheduled + 2h
        if not (event.scheduled_at - WINDOW_BEFORE <= now <= event.scheduled_at + WINDOW_AFTER):
            continue
        if event.impact is MacroImpact.MAXIMUM:
            return MacroFilterResult(
                blackout=True, caution=False, reason=f"blackout: {event.name} within window"
            )
        caution = True
    return MacroFilterResult(blackout=False, caution=caution)
