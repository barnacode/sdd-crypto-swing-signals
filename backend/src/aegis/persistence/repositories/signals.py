"""Signal-pipeline repository (T031).

Persists and reads the deterministic candidate, the AI-decided signal, its order ticket, and the
AI audit record — mapping between domain models (Decimal figures) and ORM rows. The candidate is
the numeric source of truth; reconciliation reads back from here (AC-04).
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from aegis.domain import (
    AIAudit,
    OrderTicket,
    Side,
    Signal,
    SignalCandidate,
    SignalStatus,
    Timeframe,
)
from aegis.domain.enums import EntryType, OrderStructure, TimeInForce
from aegis.persistence.models import (
    AIAuditRow,
    OrderTicketRow,
    SignalCandidateRow,
    SignalRow,
)


class SignalRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    # --- candidate ---
    async def add_candidate(self, c: SignalCandidate) -> None:
        self._s.add(
            SignalCandidateRow(
                id=c.id,
                symbol=c.symbol,
                tf=c.tf.value,
                ts=c.ts,
                side=c.side.value,
                entry=c.entry,
                stop=c.stop,
                target=c.target,
                rr=c.rr,
                score=c.score,
                features=c.features,
            )
        )

    async def get_candidate(self, candidate_id: UUID) -> SignalCandidate | None:
        row = await self._s.get(SignalCandidateRow, candidate_id)
        if row is None:
            return None
        return SignalCandidate(
            id=row.id,
            symbol=row.symbol,
            tf=Timeframe(row.tf),
            ts=row.ts,
            side=Side(row.side),
            entry=row.entry,
            stop=row.stop,
            target=row.target,
            rr=row.rr,
            score=row.score,
            features=row.features,
        )

    # --- signal ---
    async def add_signal(self, s: Signal) -> None:
        self._s.add(
            SignalRow(
                id=s.id,
                candidate_id=s.candidate_id,
                side=s.side.value,
                entry=s.entry,
                stop=s.stop,
                target=s.target,
                rr=s.rr,
                confidence=s.confidence,
                thesis=s.thesis,
                bull_case=s.bull_case,
                bear_case=s.bear_case,
                invalidation=s.invalidation,
                ai_rationale=s.ai_rationale,
                status=s.status.value,
                ts=s.ts,
            )
        )

    @staticmethod
    def _to_signal(row: SignalRow) -> Signal:
        return Signal(
            id=row.id,
            candidate_id=row.candidate_id,
            side=Side(row.side),
            entry=row.entry,
            stop=row.stop,
            target=row.target,
            rr=row.rr,
            confidence=row.confidence,
            thesis=row.thesis,
            bull_case=row.bull_case,
            bear_case=row.bear_case,
            invalidation=row.invalidation,
            ai_rationale=row.ai_rationale,
            status=SignalStatus(row.status),
            ts=row.ts,
        )

    async def get_signal(self, signal_id: UUID) -> Signal | None:
        row = await self._s.get(SignalRow, signal_id)
        return self._to_signal(row) if row is not None else None

    async def list_signals(self, *, status: str | None = None, limit: int = 100) -> list[Signal]:
        stmt = select(SignalRow).order_by(SignalRow.ts.desc()).limit(limit)
        if status is not None:
            stmt = stmt.where(SignalRow.status == status)
        rows = (await self._s.execute(stmt)).scalars().all()
        return [self._to_signal(r) for r in rows]

    # --- order ticket ---
    async def add_order_ticket(self, signal_id: UUID, t: OrderTicket) -> None:
        self._s.add(
            OrderTicketRow(
                signal_id=signal_id,
                entry_type=t.entry_type.value,
                entry_price=t.entry_price,
                quantity=t.quantity,
                notional=t.notional,
                order_structure=t.order_structure.value,
                take_profit=t.take_profit,
                sl_trigger=t.sl_trigger,
                sl_limit=t.sl_limit,
                trailing=t.trailing,
                exit_plan=t.exit_plan,
                tif=t.tif.value,
                target_exchange=t.target_exchange,
                valid_until=t.valid_until,
            )
        )

    async def get_order_ticket(self, signal_id: UUID) -> OrderTicket | None:
        row = await self._s.get(OrderTicketRow, signal_id)
        if row is None:
            return None
        return OrderTicket(
            signal_id=row.signal_id,
            entry_type=EntryType(row.entry_type),
            entry_price=row.entry_price,
            quantity=row.quantity,
            notional=row.notional,
            order_structure=OrderStructure(row.order_structure),
            take_profit=row.take_profit,
            sl_trigger=row.sl_trigger,
            sl_limit=row.sl_limit,
            trailing=row.trailing,
            exit_plan=row.exit_plan,
            tif=TimeInForce(row.tif),
            target_exchange=row.target_exchange,
            valid_until=row.valid_until,
        )

    # --- ai audit ---
    async def add_ai_audit(self, a: AIAudit) -> None:
        self._s.add(
            AIAuditRow(
                signal_id=a.signal_id,
                prompt_hash=a.prompt_hash,
                inputs=a.inputs,
                reasoning=a.reasoning,
                model=a.model,
                ts=a.ts,
            )
        )
