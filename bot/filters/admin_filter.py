"""Admin filter to restrict bot command access exclusively to administrators."""

from aiogram.filters import BaseFilter
from aiogram.types import Message
from config import Settings


class IsAdminFilter(BaseFilter):
    """Filter that checks if the incoming message is from an authorized admin."""

    async def __call__(self, message: Message, settings: Settings) -> bool:
        if not message.from_user:
            return False
        return settings.is_admin(message.from_user.id)
