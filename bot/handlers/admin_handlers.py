"""Admin command handlers for Zero to Hero English Channel Analyzer.

Handles /start, /analyze, /status, /topics, /cleanup, and /help commands.
Access is restricted strictly to administrators configured in settings.
"""

import asyncio
import logging
from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from aiogram.enums import ChatType

from config import Settings
from bot.filters.admin_filter import IsAdminFilter
from analyzer.gemini_analyzer import GeminiAnalyzer
from database.crud import (
    get_recent_posts,
    get_recent_comments,
    save_analysis,
    get_latest_analysis,
    get_db_stats,
    cleanup_old_data,
)
from database.models import AnalysisRecord
from services.reporter_service import (
    format_start_message,
    format_help_message,
    format_status_message,
    format_topics_message,
)

logger = logging.getLogger("ZeroToHeroAnalyzer.AdminHandlers")

router = Router(name="admin_handlers")


@router.message(CommandStart(), IsAdminFilter())
async def handle_start_admin(message: Message, settings: Settings) -> None:
    """Handle /start command for authorized administrators."""
    admin_name = message.from_user.first_name if message.from_user else "Administrator"
    text = format_start_message(admin_name)
    await message.answer(text, parse_mode="Markdown")


@router.message(Command("help"), IsAdminFilter())
async def handle_help_admin(message: Message, settings: Settings) -> None:
    """Handle /help command for administrators."""
    text = format_help_message()
    await message.answer(text, parse_mode="Markdown")


@router.message(Command("status"), IsAdminFilter())
async def handle_status_admin(message: Message, settings: Settings) -> None:
    """Handle /status command: reports posts, comments count and DB metrics."""
    stats = await get_db_stats(settings.DATABASE_PATH, days=2)
    ch_id = str(settings.CHANNEL_ID) if settings.CHANNEL_ID else None
    gr_id = str(settings.DISCUSSION_GROUP_ID) if settings.DISCUSSION_GROUP_ID else None
    text = format_status_message(stats, ch_id, gr_id)
    await message.answer(text, parse_mode="Markdown")


@router.message(Command("topics"), IsAdminFilter())
async def handle_topics_admin(message: Message, settings: Settings) -> None:
    """Handle /topics command: shows the most recent AI topic recommendations."""
    latest = await get_latest_analysis(settings.DATABASE_PATH)
    text = format_topics_message(latest)
    await message.answer(text, parse_mode="Markdown")


@router.message(Command("cleanup"), IsAdminFilter())
async def handle_cleanup_admin(message: Message, settings: Settings) -> None:
    """Handle /cleanup command: manually deletes data older than 2 days."""
    status_msg = await message.answer("🧹 2 kundan eski ma'lumotlar tozalanmoqda...")
    deleted_p, deleted_c = await cleanup_old_data(settings.DATABASE_PATH, days=2)
    await status_msg.edit_text(
        f"✅ **Tozalash muvaffaqiyatli yakunlandi!**\n\n"
        f"• O'chirilgan eski postlar: `{deleted_p} ta`\n"
        f"• O'chirilgan eski izohlar: `{deleted_c} ta`\n"
        f"• Baza hajmi minimal holatga keltirildi.",
        parse_mode="Markdown"
    )


@router.message(Command("analyze"), IsAdminFilter())
async def handle_analyze_admin(
    message: Message,
    settings: Settings,
    analyzer: GeminiAnalyzer
) -> None:
    """Handle /analyze command: performs 4-stage AI channel analysis."""
    logger.info(f"Admin {message.from_user.id if message.from_user else 'Unknown'} triggered /analyze")

    # Stage 1: Checking data
    status_msg = await message.answer("⏳ **[1/4] Ma'lumotlar tekshirilmoqda...**", parse_mode="Markdown")
    await asyncio.sleep(0.4)

    # Fetch last 2 days' posts and comments from SQLite
    posts = await get_recent_posts(settings.DATABASE_PATH, days=2)
    comments = await get_recent_comments(settings.DATABASE_PATH, days=2)

    # Stage 2: Preparing data
    p_count = len(posts)
    c_count = len(comments)
    await status_msg.edit_text(
        f"⏳ **[2/4] Post va kommentlar tayyorlanmoqda...**\n"
        f"*(Oxirgi 2 kunlik: {p_count} ta post, {c_count} ta izoh topildi)*",
        parse_mode="Markdown"
    )
    await asyncio.sleep(0.5)

    # Stage 3: Calling Gemini AI
    await status_msg.edit_text("⏳ **[3/4] Gemini AI tahlil qilmoqda...**", parse_mode="Markdown")

    try:
        final_text, topics_list = await analyzer.generate_topics(posts, comments)

        # Stage 4: Ready and save to DB
        record = AnalysisRecord(
            posts_analyzed_count=p_count,
            comments_analyzed_count=c_count,
            raw_topics_text=final_text,
            topics_list=topics_list
        )
        await save_analysis(settings.DATABASE_PATH, record)

        await status_msg.edit_text("✅ **[4/4] Mavzular tayyor!**", parse_mode="Markdown")
        await asyncio.sleep(0.3)

        # Send strictly the final topics list without unnecessary conversational fluff
        await message.answer(final_text, parse_mode="Markdown")
        logger.info(f"Analysis completed successfully. Generated {len(topics_list)} topics.")

    except ValueError as ve:
        logger.error(f"Configuration error during analysis: {ve}")
        await status_msg.edit_text(
            f"⚠️ **Sozlash xatosi:**\n{ve}\n\nIltimos, `.env` faylida `GEMINI_API_KEY` ni tekshiring.",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Error during AI analysis: {e}", exc_info=True)
        await status_msg.edit_text(
            f"❌ **AI tahlilida xatolik yuz berdi:**\n`{str(e)[:300]}`\n\n"
            f"Internet aloqasi yoki Gemini API kalitini tekshirib ko'ring.",
            parse_mode="Markdown"
        )


@router.message(F.chat.type == ChatType.PRIVATE)
async def handle_non_admin_private(message: Message, settings: Settings) -> None:
    """Polite notice for non-authorized users attempting to access private bot."""
    user_id = message.from_user.id if message.from_user else 0
    if not settings.is_admin(user_id):
        logger.warning(f"Unauthorized private message attempt from user ID: {user_id}")
        await message.answer(
            "🔒 Ushbu bot faqat **Zero to Hero English** kanali administratorlari uchun mo'ljallangan yopiq tahlilchi bot hisoblanadi."
        )
