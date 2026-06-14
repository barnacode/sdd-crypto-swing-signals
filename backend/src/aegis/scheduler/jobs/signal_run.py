"""Signal-run pipeline (T040 + T053 US2 safety stack): the gated US1 loop.

Deterministic gates (G1–G5) and the macro pre-event filter run BEFORE any AI call, so an unsafe
setup spends no LLM (FR-005, C-7). The AI then decides; the post-AI reconciliation rejects any
figure that does not match the candidate (AC-04, C-2); the risk-guardian vetoes on portfolio
limits (AC-10, FR-015). Emits only when every gate passes, the AI says 'emit', figures reconcile,
and risk approves. Anything else → no signal, no alert (silence > bad signal, C-4). Nothing places
an order (C-1).
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Any, Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from aegis.ai import (
    AISignalDecision,
    build_signal_from_decision,
    reconcile_signal,
    should_emit,
)
from aegis.candidates import build_order_ticket
from aegis.candidates.gates import GateInput, evaluate_gates
from aegis.candidates.macro_filter import evaluate_macro_filter
from aegis.candidates.risk_guardian import RiskInput, evaluate_risk
from aegis.domain import MacroEvent, Signal, SignalCandidate
from aegis.persistence.repositories.signals import SignalRepository
from aegis.telegram.outbound.base import MessageSender
from aegis.telegram.outbound.signal import send_signal_alert


class DecisionMaker(Protocol):
    def decide(
        self, candidates: Sequence[SignalCandidate], context: dict[str, Any]
    ) -> AISignalDecision | None: ...


async def run_signal_pipeline(
    *,
    candidate: SignalCandidate,
    context: dict[str, Any],
    orchestrator: DecisionMaker,
    session: AsyncSession,
    sender: MessageSender,
    chat_id: int,
    venue: str = "binance",
    gate_input: GateInput | None = None,
    macro_now: datetime | None = None,
    macro_events: Sequence[MacroEvent] = (),
    risk_input: RiskInput | None = None,
) -> Signal | None:
    # --- US2 deterministic gates BEFORE the AI (no LLM spend on an unsafe setup) ---
    if gate_input is not None and not evaluate_gates(gate_input).passed:
        return None
    if macro_now is not None and evaluate_macro_filter(macro_now, macro_events).blackout:
        return None

    decision = orchestrator.decide([candidate], context)
    if decision is None or not should_emit(decision):
        return None  # AI unavailable/invalid, or discard/watch — fail-safe (AC-05, C-4)

    # --- portfolio veto (after the decision, before persist/alert) ---
    if risk_input is not None and not evaluate_risk(risk_input).approved:
        return None  # bounded sizing / aggregate cap / correlation (AC-10, FR-015)

    signal = build_signal_from_decision(candidate, decision)
    ticket = build_order_ticket(candidate, venue=venue)
    if not reconcile_signal(signal, candidate, ticket).ok:
        return None  # numeric mismatch ⇒ discard + (caller records incident) (AC-04, C-2)

    repo = SignalRepository(session)
    await repo.add_signal(signal)
    await repo.add_order_ticket(signal.id, ticket)
    await session.commit()

    await send_signal_alert(
        sender, chat_id=chat_id, signal=signal, ticket=ticket, symbol=candidate.symbol
    )
    return signal
