"""Context/safety alert tests (T052, US2, AC-13/AC-17, C-14).

SECURITY_ALERT / MACRO_EVENT / SYSTEMIC_ALERT render with the disclaimer and send via the same
MessageSender. SYSTEMIC_ALERT signals the global pause.
"""

from __future__ import annotations

from aegis.telegram.outbound.context_alerts import (
    render_macro_alert,
    render_security_alert,
    render_systemic_alert,
    send_systemic_alert,
)


class _RecordingSender:
    def __init__(self):
        self.calls = []

    async def send(self, *, chat_id, text, buttons=None):
        self.calls.append({"chat_id": chat_id, "text": text})


def test_security_alert_renders():
    text = render_security_alert(asset="ETH/USDT", source="PeckShield", severity="high")
    assert "SECURITY_ALERT" in text and "ETH/USDT" in text
    assert "not financial advice" in text.lower()


def test_macro_alert_renders():
    text = render_macro_alert(event_name="FOMC", eta_hours=8, affected=["BTC/USDT"])
    assert "MACRO_EVENT" in text and "FOMC" in text and "BTC/USDT" in text


def test_systemic_alert_renders_global_pause():
    text = render_systemic_alert(flag_type="depeg", detail="USDT -1.2%")
    assert "SYSTEMIC_ALERT" in text and "pause" in text.lower()


async def test_send_systemic_alert():
    sender = _RecordingSender()
    await send_systemic_alert(sender, chat_id=9, flag_type="depeg", detail="USDT -1.2%")
    assert len(sender.calls) == 1 and sender.calls[0]["chat_id"] == 9
