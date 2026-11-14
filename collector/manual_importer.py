"""Manual importer handler for Zero to Hero English Channel Analyzer.

Allows administrators to backfill recent historical posts and comments by
simply forwarding them to the bot in private chat.
"""

from datetime import datetime, timezone
import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.enums import ChatType

from config import Settings
from database.crud import save_post, save_comment
from database.models import ChannelPost, PostComment
from collector.channel_collector import detect_media_type, extract_post_content

logger = logging.getLogger("ZeroToHeroAnalyzer.ManualImporter")

router = Router(name="manual_importer")


@router.message(F.chat.type == ChatType.PRIVATE, F.forward_origin | F.forward_from_chat | F.forward_from)
async def handle_forwarded_message(message: Message, settings: Settings) -> None:
    """Import forwarded post or comment from administrator in private chat."""
    if not settings.is_admin(message.from_user.id if message.from_user else 0):
        # Non-admins cannot import
        return

    # Check Telegram 7.0+ forward_origin or legacy fields
    is_channel_post = False
    original_channel_id = 0
    original_message_id = 0
    orig_date = message.date.astimezone(timezone.utc) if message.date else datetime.now(timezone.utc)
    author_name = "Forwarded"

    if hasattr(message, "forward_origin") and message.forward_origin:
        origin = message.forward_origin
        origin_type = getattr(origin, "type", "")
        if origin_type == "channel":
            is_channel_post = True
            chat_obj = getattr(origin, "chat", None)
            if chat_obj:
                original_channel_id = chat_obj.id
            original_message_id = getattr(origin, "message_id", message.message_id)
            if hasattr(origin, "date") and origin.date:
                orig_date = origin.date.astimezone(timezone.utc)
        elif origin_type in {"user", "hidden_user"}:
            is_channel_post = False
            user_obj = getattr(origin, "sender_user", None)
            if user_obj:
                author_name = user_obj.full_name
            original_message_id = message.message_id
    elif message.forward_from_chat:
        # Legacy aiogram field
        if message.forward_from_chat.type == "channel":
            is_channel_post = True
            original_channel_id = message.forward_from_chat.id
            original_message_id = message.forward_from_message_id or message.message_id
            if message.forward_date:
                orig_date = message.forward_date.astimezone(timezone.utc)

    if is_channel_post:
        media_type = detect_media_type(message)
        content = extract_post_content(message)
        post = ChannelPost(
            message_id=original_message_id,
            channel_id=original_channel_id or (int(settings.CHANNEL_ID) if str(settings.CHANNEL_ID or "").lstrip("-").isdigit() else 0),
            text=content,
            media_type=media_type,
            views=getattr(message, "views", 0) or 0,
            date=orig_date
        )
        saved = await save_post(settings.DATABASE_PATH, post)
        date_str = orig_date.strftime("%Y-%m-%d %H:%M")
        if saved:
            await message.reply(
                f"📥 **Kanal posti bazaga qo'shildi!**\n"
                f"• ID: `#{original_message_id}`\n"
                f"• Turi: `{media_type}`\n"
                f"• Sanasi: `{date_str}`\n"
                f"• Matn: {content[:100]}..."
            )
        else:
            await message.reply(f"ℹ️ Post `#{original_message_id}` yangilandi.")
    else:
        # User comment / message import
        comment_text = message.text or message.caption or "[Media xabar]"
        comment = PostComment(
            message_id=message.message_id,
            chat_id=message.chat.id,
            reply_to_post_id=None,
            text=comment_text,
            user_fullname=author_name,
            date=orig_date
        )
        saved = await save_comment(settings.DATABASE_PATH, comment)
        if saved:
            await message.reply(
                f"💬 **Izoh/savol bazaga qo'shildi!**\n"
                f"• Muallif: `{author_name}`\n"
                f"• Matn: {comment_text[:100]}"
            )
        else:
            await message.reply("ℹ️ Bu izoh allaqachon mavjud.")
