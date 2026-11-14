"""CRUD (Create, Read, Update, Delete) operations for SQLite database."""

from datetime import datetime, timedelta, timezone
import logging
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
import aiosqlite

from database.models import ChannelPost, PostComment, AnalysisRecord

logger = logging.getLogger("ZeroToHeroAnalyzer.CRUD")


def _get_cutoff_iso(days: int = 2) -> str:
    """Return ISO format string for cutoff date (UTC)."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    return cutoff.strftime("%Y-%m-%d %H:%M:%S")


async def save_post(db_path: Path, post: ChannelPost) -> bool:
    """Insert or update a channel post in the database.

    Returns True if a new row was inserted, False if updated or skipped.
    """
    sql = """
    INSERT INTO posts (message_id, channel_id, text, media_type, topic, views, forwards, date)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(channel_id, message_id) DO UPDATE SET
        text = excluded.text,
        media_type = excluded.media_type,
        topic = excluded.topic,
        views = excluded.views,
        forwards = excluded.forwards,
        date = excluded.date;
    """
    dt_str = post.date.strftime("%Y-%m-%d %H:%M:%S") if isinstance(post.date, datetime) else str(post.date)
    try:
        async with aiosqlite.connect(str(db_path)) as db:
            cursor = await db.execute(
                sql,
                (
                    post.message_id,
                    post.channel_id,
                    post.text,
                    post.media_type,
                    post.topic,
                    post.views or 0,
                    post.forwards or 0,
                    dt_str
                )
            )
            await db.commit()
            return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Failed to save post #{post.message_id}: {e}", exc_info=True)
        return False


async def save_comment(db_path: Path, comment: PostComment) -> bool:
    """Insert a comment into the database if not already present.

    Returns True if inserted, False if already exists or on error.
    """
    sql = """
    INSERT OR IGNORE INTO comments (
        message_id, chat_id, reply_to_post_id, text, user_id, user_fullname, user_username, date
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """
    dt_str = comment.date.strftime("%Y-%m-%d %H:%M:%S") if isinstance(comment.date, datetime) else str(comment.date)
    try:
        async with aiosqlite.connect(str(db_path)) as db:
            cursor = await db.execute(
                sql,
                (
                    comment.message_id,
                    comment.chat_id,
                    comment.reply_to_post_id,
                    comment.text,
                    comment.user_id,
                    comment.user_fullname,
                    comment.user_username,
                    dt_str
                )
            )
            await db.commit()
            return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Failed to save comment #{comment.message_id}: {e}", exc_info=True)
        return False


async def get_recent_posts(db_path: Path, days: int = 2) -> List[ChannelPost]:
    """Retrieve posts from the last `days` days."""
    cutoff = _get_cutoff_iso(days)
    sql = """
    SELECT id, message_id, channel_id, text, media_type, topic, views, forwards, date, created_at
    FROM posts
    WHERE date >= ?
    ORDER BY date ASC;
    """
    posts: List[ChannelPost] = []
    try:
        async with aiosqlite.connect(str(db_path)) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(sql, (cutoff,)) as cursor:
                async for row in cursor:
                    try:
                        dt = datetime.fromisoformat(row["date"])
                    except Exception:
                        dt = datetime.utcnow()
                    posts.append(
                        ChannelPost(
                            id=row["id"],
                            message_id=row["message_id"],
                            channel_id=row["channel_id"],
                            text=row["text"],
                            media_type=row["media_type"],
                            topic=row["topic"],
                            views=row["views"],
                            forwards=row["forwards"],
                            date=dt
                        )
                    )
    except Exception as e:
        logger.error(f"Failed to get recent posts: {e}", exc_info=True)
    return posts


async def get_recent_comments(db_path: Path, days: int = 2) -> List[PostComment]:
    """Retrieve comments from the last `days` days."""
    cutoff = _get_cutoff_iso(days)
    sql = """
    SELECT id, message_id, chat_id, reply_to_post_id, text, user_id, user_fullname, user_username, date, created_at
    FROM comments
    WHERE date >= ?
    ORDER BY date ASC;
    """
    comments: List[PostComment] = []
    try:
        async with aiosqlite.connect(str(db_path)) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(sql, (cutoff,)) as cursor:
                async for row in cursor:
                    try:
                        dt = datetime.fromisoformat(row["date"])
                    except Exception:
                        dt = datetime.utcnow()
                    comments.append(
                        PostComment(
                            id=row["id"],
                            message_id=row["message_id"],
                            chat_id=row["chat_id"],
                            reply_to_post_id=row["reply_to_post_id"],
                            text=row["text"],
                            user_id=row["user_id"],
                            user_fullname=row["user_fullname"],
                            user_username=row["user_username"],
                            date=dt
                        )
                    )
    except Exception as e:
        logger.error(f"Failed to get recent comments: {e}", exc_info=True)
    return comments


async def cleanup_old_data(db_path: Path, days: int = 2) -> Tuple[int, int]:
    """Delete posts and comments older than `days` days.

    Returns tuple (deleted_posts_count, deleted_comments_count).
    """
    cutoff = _get_cutoff_iso(days)
    deleted_posts = 0
    deleted_comments = 0
    try:
        async with aiosqlite.connect(str(db_path)) as db:
            c1 = await db.execute("DELETE FROM posts WHERE date < ?;", (cutoff,))
            deleted_posts = c1.rowcount
            c2 = await db.execute("DELETE FROM comments WHERE date < ?;", (cutoff,))
            deleted_comments = c2.rowcount
            await db.commit()
            if deleted_posts > 0 or deleted_comments > 0:
                logger.info(
                    f"2-day auto-cleanup executed: deleted {deleted_posts} posts and {deleted_comments} comments older than {cutoff}."
                )
    except Exception as e:
        logger.error(f"Failed during cleanup_old_data: {e}", exc_info=True)
    return deleted_posts, deleted_comments


async def save_analysis(db_path: Path, record: AnalysisRecord) -> int:
    """Save AI analysis topics recommendation to database."""
    sql = """
    INSERT INTO analyzed_topics (posts_analyzed_count, comments_analyzed_count, raw_topics_text, topics_list_json)
    VALUES (?, ?, ?, ?);
    """
    try:
        async with aiosqlite.connect(str(db_path)) as db:
            cursor = await db.execute(
                sql,
                (
                    record.posts_analyzed_count,
                    record.comments_analyzed_count,
                    record.raw_topics_text,
                    record.topics_json
                )
            )
            await db.commit()
            return cursor.lastrowid or 0
    except Exception as e:
        logger.error(f"Failed to save analysis record: {e}", exc_info=True)
        return 0


async def get_latest_analysis(db_path: Path) -> Optional[AnalysisRecord]:
    """Retrieve the most recent AI analysis record from database."""
    sql = """
    SELECT id, created_at, posts_analyzed_count, comments_analyzed_count, raw_topics_text, topics_list_json
    FROM analyzed_topics
    ORDER BY id DESC
    LIMIT 1;
    """
    try:
        async with aiosqlite.connect(str(db_path)) as db:
            async with db.execute(sql) as cursor:
                row = await cursor.fetchone()
                if row:
                    return AnalysisRecord.from_row(tuple(row))
    except Exception as e:
        logger.error(f"Failed to get latest analysis: {e}", exc_info=True)
    return None


async def get_db_stats(db_path: Path, days: int = 2) -> Dict[str, Any]:
    """Calculate statistics of collected posts, comments and database size."""
    cutoff = _get_cutoff_iso(days)
    stats: Dict[str, Any] = {
        "recent_posts_count": 0,
        "recent_comments_count": 0,
        "total_posts_count": 0,
        "total_comments_count": 0,
        "latest_post_date": None,
        "latest_comment_date": None,
        "db_size_kb": 0.0,
    }

    if db_path.exists():
        stats["db_size_kb"] = round(db_path.stat().st_size / 1024, 2)

    try:
        async with aiosqlite.connect(str(db_path)) as db:
            db.row_factory = aiosqlite.Row

            # Recent posts
            async with db.execute("SELECT COUNT(*), MAX(date) FROM posts WHERE date >= ?;", (cutoff,)) as c:
                row = await c.fetchone()
                if row:
                    stats["recent_posts_count"] = row[0] or 0
                    stats["latest_post_date"] = row[1]

            # Recent comments
            async with db.execute("SELECT COUNT(*), MAX(date) FROM comments WHERE date >= ?;", (cutoff,)) as c:
                row = await c.fetchone()
                if row:
                    stats["recent_comments_count"] = row[0] or 0
                    stats["latest_comment_date"] = row[1]

            # Total all-time (if any before cleanup)
            async with db.execute("SELECT COUNT(*) FROM posts;") as c:
                row = await c.fetchone()
                if row:
                    stats["total_posts_count"] = row[0] or 0

            async with db.execute("SELECT COUNT(*) FROM comments;") as c:
                row = await c.fetchone()
                if row:
                    stats["total_comments_count"] = row[0] or 0

    except Exception as e:
        logger.error(f"Failed to calculate db stats: {e}", exc_info=True)

    return stats
