"""Signals read API + internal AI publish path (T039, AC-04/AC-09, FR-023).

All routes require the API key. The AI publishes a decided signal to ``/internal/signals``; the
endpoint reconciles every figure against the persisted candidate (409 on mismatch, AC-04) before
persisting. There is NO order-execution route anywhere (C-1, FR-023).
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from aegis.ai.reconciliation import reconcile_signal
from aegis.api.deps import get_session, require_api_key
from aegis.domain import Signal
from aegis.persistence.repositories.signals import SignalRepository

router = APIRouter(dependencies=[Depends(require_api_key)])


@router.get("/signals")
async def list_signals(
    status_filter: str | None = Query(default=None, alias="status"),
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, Any]]:
    repo = SignalRepository(session)
    signals = await repo.list_signals(status=status_filter)
    return [s.model_dump(mode="json") for s in signals]


@router.get("/signals/{signal_id}")
async def get_signal(
    signal_id: UUID, session: AsyncSession = Depends(get_session)
) -> dict[str, Any]:
    signal = await SignalRepository(session).get_signal(signal_id)
    if signal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="signal not found")
    return signal.model_dump(mode="json")


@router.get("/signals/{signal_id}/order")
async def get_order_ticket(
    signal_id: UUID, session: AsyncSession = Depends(get_session)
) -> dict[str, Any]:
    ticket = await SignalRepository(session).get_order_ticket(signal_id)
    if ticket is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="order ticket not found")
    return ticket.model_dump(mode="json")


@router.post("/internal/signals", status_code=status.HTTP_201_CREATED)
async def publish_signal(
    signal: Signal, session: AsyncSession = Depends(get_session)
) -> dict[str, Any]:
    repo = SignalRepository(session)
    candidate = await repo.get_candidate(signal.candidate_id)
    if candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="candidate not found")
    result = reconcile_signal(signal, candidate)
    if not result.ok:
        # Determinism boundary: reject hallucinated figures, record the incident (AC-04, C-2).
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "reconciliation mismatch", "reasons": list(result.reasons)},
        )
    await repo.add_signal(signal)
    await session.commit()
    return signal.model_dump(mode="json")
