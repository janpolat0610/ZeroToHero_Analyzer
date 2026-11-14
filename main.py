"""Main entry point for Zero to Hero English — AI Channel Analyzer Bot.

Strictly standalone, isolated from existing bots, running exclusively on D: drive.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import load_config, setup_logging, Settings
from database.db import init_database
from database.crud import cleanup_old_data
from analyzer.gemini_analyzer import GeminiAnalyzer
from bot.handlers.admin_handlers import router as admin_router
from collector.channel_collector import router as channel_router
from collector.comment_collector import router as comment_router
from collector.manual_importer import router as importer_router
from bot.middlewares.logging_middleware import LoggingAndContextMiddleware
from services.scheduler_service import setup_scheduler


async def main() -> None:
    """Initialize all subsystems and start bot polling."""
    # 1. Load settings from D:\ZeroToHero_Analyzer\.env
    try:
        settings: Settings = load_config()
    except Exception as e:
        print(f"FATAL: Failed to load configuration from .env: {e}")
        print("Iltimos, D:\\ZeroToHero_Analyzer\\.env faylini yaratib, BOT_TOKEN va GEMINI_API_KEY ni kiriting.")
        sys.exit(1)

    # 2. Setup logging to D:\ZeroToHero_Analyzer\logs\bot.log
    logger = setup_logging(settings)
    logger.info("==================================================================")
    logger.info("Starting Zero to Hero English — AI Channel Analyzer Bot")
    logger.info("Project Root: D:\\ZeroToHero_Analyzer")
    logger.info(f"Database Path: {settings.DATABASE_PATH}")
    logger.info(f"Log File Path: {settings.LOG_FILE_PATH}")
    logger.info("==================================================================")

    # 3. Initialize SQLite database schema
    await init_database(settings.DATABASE_PATH)

    # 4. Initial cleanup of data older than 2 days
    deleted_p, deleted_c = await cleanup_old_data(settings.DATABASE_PATH, days=2)
    logger.info(f"Startup 2-day cleanup: purged {deleted_p} old posts and {deleted_c} old comments.")

    # 5. Initialize Gemini AI Analyzer
    analyzer = GeminiAnalyzer(
        api_key=settings.GEMINI_API_KEY,
        model_name=settings.GEMINI_MODEL
    )

    # 6. Initialize Bot and Dispatcher
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
    )
    dp = Dispatcher()

    # 7. Register Middlewares
    dp.update.middleware(LoggingAndContextMiddleware(settings))

    # 8. Dependency injection into workflow data
    dp["analyzer"] = analyzer
    dp["settings"] = settings

    # 9. Register Routers (Order matters: admin commands -> manual importer -> collector)
    dp.include_router(admin_router)
    dp.include_router(importer_router)
    dp.include_router(channel_router)
    dp.include_router(comment_router)

    # 10. Start APScheduler background maintenance
    scheduler = setup_scheduler(settings)
    scheduler.start()
    logger.info("APScheduler background cleanup service started.")

    # 11. Delete any pending webhook updates and start long-polling
    try:
        # Check bot identity
        bot_info = await bot.get_me()
        logger.info(f"Bot connected successfully as: @{bot_info.username} (ID: {bot_info.id})")
        logger.info(f"Authorized Admins: {settings.ADMIN_IDS}")

        # Drop pending updates to avoid old backlog processing
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Bot is now listening for channel posts, discussion comments, and /analyze...")

        # Start polling
        await dp.start_polling(
            bot,
            allowed_updates=["message", "edited_message", "channel_post", "edited_channel_post"]
        )
    except Exception as e:
        logger.critical(f"Bot execution error: {e}", exc_info=True)
    finally:
        logger.info("Shutting down bot and closing background services...")
        if scheduler.running:
            scheduler.shutdown()
        await bot.session.close()
        logger.info("Bot shutdown completed cleanly.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\nBot to'xtatildi.")
