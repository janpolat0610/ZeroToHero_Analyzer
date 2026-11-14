"""Channel post collector for Zero to Hero English Channel Analyzer.

Listens to channel_post and edited_channel_post updates from Telegram.
"""

from datetime import datetime, timezone
import logging
from typing import Optional
from aiogram import Router, F
from aiogram.types import Message

from config import Settings
from database.crud import save_post
from database.models import ChannelPost

logger = logging.getLogger("ZeroToHeroAnalyzer.ChannelCollector")

router = Router(name="channel_collector")


def detect_media_type(message: Message) -> str:
    """Detect content/media type of the channel message."""
    if message.text:
        return "text"
    elif message.photo:
        return "photo"
    elif message.video:
        return "video"
    elif message.document:
        return "document"
    elif message.poll:
        return "poll"
    elif message.audio:
        return "audio"
    elif message.voice:
        return "voice"
    elif message.animation:
        return "animation"
    return "other"


def extract_post_content(message: Message) -> str:
    """Extract readable text or caption from channel message."""
    if message.text:
        return message.text
    if message.caption:
        return message.caption
    if message.poll:
        options = [opt.text for opt in message.poll.options]
        return f"So'rovnoma: {message.poll.question} | Variantlar: {', '.join(options)}"
    if message.document:
        name = message.document.file_name or "Hujjat"
        return f"Hujjat: {name}"
    return f"[{detect_media_type(message).capitalize()} media posti]"


@router.channel_post()
@router.edited_channel_post()
async def handle_channel_post(message: Message, settings: Settings) -> None:
    """Handle incoming or edited post directly from the channel."""
    chat_id = message.chat.id
    chat_username = message.chat.username

    # Filter by configured channel if set
    if settings.CHANNEL_ID:
        target = str(settings.CHANNEL_ID).strip()
        matched = False
        if target.startswith("@") and chat_username:
            matched = (chat_username.lower() == target.lstrip("@").lower())
        else:
            try:
                matched = (chat_id == int(target))
            except ValueError:
                pass

        if not matched:
            logger.debug(f"Ignoring post from channel {chat_id} (@{chat_username}), not matching {target}")
            return

    media_type = detect_media_type(message)
    content = extract_post_content(message)
    msg_date = message.date.astimezone(timezone.utc) if message.date else datetime.now(timezone.utc)

    views = getattr(message, "views", 0) or 0
    forwards = getattr(message, "forward_count", 0) or 0

    post = ChannelPost(
        message_id=message.message_id,
        channel_id=chat_id,
        text=content,
        media_type=media_type,
        views=views,
        forwards=forwards,
        date=msg_date
    )

    success = await save_post(settings.DATABASE_PATH, post)
    if success:
        logger.info(
            f"✅ Saved channel post #{message.message_id} from '{message.chat.title}' "
            f"({media_type}, views: {views}, date: {msg_date.strftime('%Y-%m-%d %H:%M')})"
        )
    else:
        logger.debug(f"Post #{message.message_id} was updated or already exists.")
