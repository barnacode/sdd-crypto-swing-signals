"""SIGNAL alert rendering + delivery (T038, FR-019/FR-026, AC-09, C-10).

Renders the English Telegram message with the copy-paste order ticket and the mandatory
"not financial advice" disclaimer, and sends it with inline take/ignore buttons. Advisory only —
no order is placed (C-1).
"""

from __future__ import annotations

from aegis.domain import OrderTicket, Signal
from aegis.telegram.outbound.base import MessageSender

DISCLAIMER = "⚠️ Not financial advice. You place and manage the order manually."


def render_signal_alert(signal: Signal, ticket: OrderTicket, symbol: str) -> str:
    return "\n".join(
        [
            f"🟢 SIGNAL — {symbol} {signal.side.value}"
            f"   confidence {signal.confidence}/100   R:R {signal.rr}",
            f"Thesis: {signal.thesis}  (bull: {signal.bull_case} / bear: {signal.bear_case})",
            f"Invalidation: {signal.invalidation}",
            "",
            f"ORDER TICKET ({ticket.order_structure.value} @ {ticket.target_exchange})",
            f"  Entry {ticket.entry_type.value} {ticket.entry_price}",
            f"  Size  {ticket.quantity} ({ticket.notional} EUR)",
            f"  TP    {ticket.take_profit}   SL {ticket.sl_trigger}/{ticket.sl_limit}",
            f"  TIF   {ticket.tif.value}   valid until {ticket.valid_until.isoformat()}",
            "",
            DISCLAIMER,
        ]
    )


def signal_buttons(signal: Signal) -> list[tuple[str, str]]:
    return [("✅ Taken", f"taken:{signal.id}"), ("❌ Ignored", f"ignored:{signal.id}")]


async def send_signal_alert(
    sender: MessageSender,
    *,
    chat_id: int,
    signal: Signal,
    ticket: OrderTicket,
    symbol: str,
) -> None:
    await sender.send(
        chat_id=chat_id,
        text=render_signal_alert(signal, ticket, symbol),
        buttons=signal_buttons(signal),
    )
