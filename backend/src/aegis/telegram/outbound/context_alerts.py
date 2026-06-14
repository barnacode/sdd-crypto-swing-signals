"""Context/safety Telegram alerts (T052, US2, AC-02/AC-13/AC-17, C-14).

SECURITY_ALERT (asset under exploit), MACRO_EVENT (max-impact event ≤ 12h with affected open
positions), SYSTEMIC_ALERT (depeg / exchange incident → global pause). All carry the disclaimer
(C-10); none places an order (C-1).
"""

from __future__ import annotations

from collections.abc import Sequence

from aegis.telegram.outbound.base import MessageSender
from aegis.telegram.outbound.signal import DISCLAIMER


def render_security_alert(*, asset: str, source: str, severity: str) -> str:
    return "\n".join(
        [
            f"🔒 SECURITY_ALERT — {asset}",
            f"Source: {source}   Severity: {severity}",
            "LONG signals are suppressed for this asset until cleared.",
            DISCLAIMER,
        ]
    )


def render_macro_alert(*, event_name: str, eta_hours: int, affected: Sequence[str]) -> str:
    affected_str = ", ".join(affected) if affected else "none"
    return "\n".join(
        [
            f"📅 MACRO_EVENT — {event_name} in ~{eta_hours}h",
            f"Affected open positions: {affected_str}",
            "Consider protecting exposed positions; new LONGs are in blackout.",
            DISCLAIMER,
        ]
    )


def render_systemic_alert(*, flag_type: str, detail: str) -> str:
    return "\n".join(
        [
            f"🛑 SYSTEMIC_ALERT — {flag_type}: {detail}",
            "Global pause active: all signals suppressed until normalization.",
            DISCLAIMER,
        ]
    )


async def send_security_alert(
    sender: MessageSender, *, chat_id: int, asset: str, source: str, severity: str
) -> None:
    await sender.send(
        chat_id=chat_id, text=render_security_alert(asset=asset, source=source, severity=severity)
    )


async def send_macro_alert(
    sender: MessageSender,
    *,
    chat_id: int,
    event_name: str,
    eta_hours: int,
    affected: Sequence[str],
) -> None:
    await sender.send(
        chat_id=chat_id,
        text=render_macro_alert(event_name=event_name, eta_hours=eta_hours, affected=affected),
    )


async def send_systemic_alert(
    sender: MessageSender, *, chat_id: int, flag_type: str, detail: str
) -> None:
    await sender.send(
        chat_id=chat_id, text=render_systemic_alert(flag_type=flag_type, detail=detail)
    )
