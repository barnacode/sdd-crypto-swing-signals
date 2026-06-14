"""Post-AI numeric reconciliation (T035, AC-04, C-2).

The signal is BUILT from the persisted candidate's figures (the AI never originates a number),
then reconciled: every figure in the signal and order ticket must equal the candidate exactly.
Any mismatch -> not OK, with reasons; the caller discards the signal and records the incident.
"""

from __future__ import annotations

from dataclasses import dataclass

from aegis.ai.failsafe import AISignalDecision
from aegis.domain import OrderTicket, Signal, SignalCandidate, SignalStatus


@dataclass(frozen=True)
class ReconciliationResult:
    ok: bool
    reasons: tuple[str, ...]


def build_signal_from_decision(
    candidate: SignalCandidate, decision: AISignalDecision
) -> Signal:
    """Construct the emitted signal using the CANDIDATE's figures (C-2).

    The AI contributes judgment (confidence, thesis, cases, invalidation) only — never numbers.
    """
    return Signal(
        candidate_id=candidate.id,
        side=candidate.side,
        entry=candidate.entry,
        stop=candidate.stop,
        target=candidate.target,
        rr=candidate.rr,
        confidence=decision.confidence,
        thesis=decision.thesis,
        bull_case=decision.bull_case,
        bear_case=decision.bear_case,
        invalidation=decision.invalidation,
        ai_rationale=f"{decision.bull_case} | {decision.bear_case}",
        status=SignalStatus.EMITTED,
        ts=candidate.ts,
    )


def reconcile_signal(
    signal: Signal,
    candidate: SignalCandidate,
    ticket: OrderTicket | None = None,
) -> ReconciliationResult:
    """Verify every figure equals the persisted candidate (AC-04)."""
    reasons: list[str] = []

    if signal.candidate_id != candidate.id:
        reasons.append("candidate_id mismatch")
    for field in ("side", "entry", "stop", "target", "rr"):
        if getattr(signal, field) != getattr(candidate, field):
            reasons.append(f"signal.{field} != candidate.{field}")

    if ticket is not None:
        ticket_checks = {
            "entry_price": candidate.entry,
            "take_profit": candidate.target,
            "sl_trigger": candidate.stop,
        }
        for field, expected in ticket_checks.items():
            if getattr(ticket, field) != expected:
                reasons.append(f"ticket.{field} != candidate value")

    return ReconciliationResult(ok=not reasons, reasons=tuple(reasons))
