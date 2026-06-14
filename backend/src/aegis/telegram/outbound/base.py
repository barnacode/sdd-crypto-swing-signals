"""Telegram message sender (T038).

A thin ``MessageSender`` protocol so outbound rendering can be tested without a token, plus the
aiogram v3 implementation. No code here ever touches an exchange (C-1).
"""

from __future__ import annotations

from typing import Protocol

from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


class MessageSender(Protocol):
    async def send(
        self, *, chat_id: int, text: str, buttons: list[tuple[str, str]] | None = None
    ) -> None: ...


class AiogramSender:
    """Sends to a single private chat via aiogram v3."""

    def __init__(self, bot: Bot) -> None:
        self._bot = bot

    async def send(
        self, *, chat_id: int, text: str, buttons: list[tuple[str, str]] | None = None
    ) -> None:
        markup: InlineKeyboardMarkup | None = None
        if buttons:
            row = [InlineKeyboardButton(text=label, callback_data=data) for label, data in buttons]
            markup = InlineKeyboardMarkup(inline_keyboard=[row])
        await self._bot.send_message(chat_id=chat_id, text=text, reply_markup=markup)
