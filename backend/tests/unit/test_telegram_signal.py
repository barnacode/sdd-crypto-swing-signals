"""Telegram SIGNAL alert tests (T038, FR-019/FR-026, AC-09, C-1/C-10).

The rendered message carries the order ticket and the mandatory disclaimer; the send path emits
the inline take/ignore buttons. Tested with a fake sender and a fake aiogram bot — no token.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from aegis.ai import build_signal_from_decision, parse_ai_decision
from aegis.candidates import build_order_ticket
from aegis.domain import Side, SignalCandidate, Timeframe
from aegis.telegram.outbound.base import AiogramSender
from aegis.telegram.outbound.signal import render_signal_alert, send_signal_alert


def _candidate() -> SignalCandidate:
    return SignalCandidate(
        symbol="BTC/USDT",
        tf=Timeframe.H1,
        ts=datetime(2026, 6, 14, tzinfo=UTC),
        side=Side.LONG,
        entry=Decimal("100"),
        stop=Decimal("96"),
        target=Decimal("108"),
        rr=Decimal("2.0"),
        score=72,
    )


def _signal_and_ticket():
    c = _candidate()
    decision = parse_ai_decision(
        {
            "decision": "emit", "entry": "100", "stop": "96", "target": "108", "rr": "2.0",
            "confidence": 72, "thesis": "breakout", "bull_case": "trend",
            "bear_case": "macro", "invalidation": "below 96",
        }
    )
    assert decision is not None
    return build_signal_from_decision(c, decision), build_order_ticket(c), c.symbol


class _RecordingSender:
    def __init__(self):
        self.calls = []

    async def send(self, *, chat_id, text, buttons=None):
        self.calls.append({"chat_id": chat_id, "text": text, "buttons": buttons})


def test_render_contains_ticket_and_disclaimer():
    signal, ticket, symbol = _signal_and_ticket()
    text = render_signal_alert(signal, ticket, symbol)
    assert "BTC/USDT" in text
    assert "LONG" in text
    assert "72" in text  # confidence
    assert str(ticket.take_profit) in text and str(ticket.sl_trigger) in text
    assert "not financial advice" in text.lower()  # C-10 / FR-026


async def test_send_emits_text_and_inline_buttons():
    signal, ticket, symbol = _signal_and_ticket()
    sender = _RecordingSender()
    await send_signal_alert(sender, chat_id=123, signal=signal, ticket=ticket, symbol=symbol)
    assert len(sender.calls) == 1
    call = sender.calls[0]
    assert call["chat_id"] == 123
    labels = [b[0] for b in call["buttons"]]
    assert any("Taken" in label for label in labels)
    assert any("Ignored" in label for label in labels)
    assert str(signal.id) in call["buttons"][0][1]  # callback carries the signal id


async def test_aiogram_sender_calls_bot():
    captured = {}

    class _FakeBot:
        async def send_message(self, *, chat_id, text, reply_markup=None):
            captured.update(chat_id=chat_id, text=text, markup=reply_markup)

    await AiogramSender(_FakeBot()).send(
        chat_id=7, text="hi", buttons=[("✅ Taken", "taken:1"), ("❌ Ignored", "ignored:1")]
    )
    assert captured["chat_id"] == 7
    assert captured["markup"] is not None  # inline keyboard built
