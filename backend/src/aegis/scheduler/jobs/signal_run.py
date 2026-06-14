"""Signal-run pipeline (T040): the US1 loop wiring.

candidate → AI decision → build signal + order ticket → post-AI reconciliation → persist → Telegram
alert. Emits only on a valid 'emit' decision whose figures reconcile with the candidate; anything
else (AI unavailable/invalid, discard/watch, numeric mismatch) yields no signal and no alert —
silence beats a bad signal (C-4/AC-05), and no hallucinated figure is emitted (C-2/AC-04).

The APScheduler trigger (per candle close) calls this for each candidate; scheduling itself is the
foundational scheduler task. Nothing here places an order (C-1).
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from aegis.ai import (
    AISignalDecision,
    build_signal_from_decision,
    reconcile_signal,
    should_emit,
)
from aegis.candidates import build_order_ticket
from aegis.domain import Signal, SignalCandidate
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
) -> Signal | None:
    decision = orchestrator.decide([candidate], context)
    if decision is None or not should_emit(decision):
        return None  # AI unavailable/invalid, or discard/watch — fail-safe (AC-05, C-4)

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
