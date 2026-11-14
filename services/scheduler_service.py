"""Background scheduler for periodic maintenance and 2-day data auto-cleanup."""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import Settings
from database.crud import cleanup_old_data

logger = logging.getLogger("ZeroToHeroAnalyzer.Scheduler")


def setup_scheduler(settings: Settings) -> AsyncIOScheduler:
    """Configure APScheduler to clean up data older than 2 days periodically."""
    scheduler = AsyncIOScheduler()

    async def periodic_cleanup_job():
        try:
            logger.info("Running scheduled 2-day data cleanup job...")
            deleted_p, deleted_c = await cleanup_old_data(settings.DATABASE_PATH, days=2)
            if deleted_p > 0 or deleted_c > 0:
                logger.info(f"Scheduled cleanup finished: removed {deleted_p} posts and {deleted_c} comments.")
        except Exception as e:
            logger.error(f"Error in periodic_cleanup_job: {e}", exc_info=True)

    scheduler.add_job(
        periodic_cleanup_job,
        trigger="interval",
        hours=max(1, settings.CLEANUP_INTERVAL_HOURS),
        id="cleanup_2days_job",
        replace_existing=True
    )

    return scheduler
