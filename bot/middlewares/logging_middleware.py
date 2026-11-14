"""Middleware for update logging and dependency injection."""

import logging
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

from config import Settings

logger = logging.getLogger("ZeroToHeroAnalyzer.Middleware")


class LoggingAndContextMiddleware(BaseMiddleware):
    """Logs incoming updates and passes settings to event handlers."""

    def __init__(self, settings: Settings):
        super().__init__()
        self.settings = settings

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        data["settings"] = self.settings

        if isinstance(event, Update):
            if event.message:
                m = event.message
                user = f"@{m.from_user.username}" if m.from_user and m.from_user.username else f"ID:{m.from_user.id if m.from_user else 'Unknown'}"
                chat_type = m.chat.type
                text = (m.text or m.caption or "")[:50]
                logger.debug(f"Update [Message] from {user} in {chat_type} (#{m.chat.id}): {text}")
            elif event.channel_post:
                p = event.channel_post
                logger.debug(f"Update [ChannelPost] #{p.message_id} in channel #{p.chat.id}")

        return await handler(event, data)
