"""Database connection and initialization module using aiosqlite."""

import logging
from pathlib import Path
import aiosqlite

logger = logging.getLogger("ZeroToHeroAnalyzer.Database")

SCHEMA_SQL = """
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;

-- Table for channel posts
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER NOT NULL,
    channel_id INTEGER NOT NULL,
    text TEXT,
    media_type TEXT DEFAULT 'text',
    topic TEXT,
    views INTEGER DEFAULT 0,
    forwards INTEGER DEFAULT 0,
    date TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(channel_id, message_id)
);

CREATE INDEX IF NOT EXISTS idx_posts_date ON posts(date);
CREATE INDEX IF NOT EXISTS idx_posts_channel_msg ON posts(channel_id, message_id);

-- Table for comments and questions
CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER NOT NULL,
    chat_id INTEGER NOT NULL,
    reply_to_post_id INTEGER,
    text TEXT NOT NULL,
    user_id INTEGER,
    user_fullname TEXT,
    user_username TEXT,
    date TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(chat_id, message_id)
);

CREATE INDEX IF NOT EXISTS idx_comments_date ON comments(date);
CREATE INDEX IF NOT EXISTS idx_comments_reply ON comments(reply_to_post_id);
CREATE INDEX IF NOT EXISTS idx_comments_chat_msg ON comments(chat_id, message_id);

-- Table for AI generated topics history
CREATE TABLE IF NOT EXISTS analyzed_topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    posts_analyzed_count INTEGER NOT NULL,
    comments_analyzed_count INTEGER NOT NULL,
    raw_topics_text TEXT NOT NULL,
    topics_list_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_analyzed_topics_created ON analyzed_topics(created_at);
"""


async def get_db_connection(db_path: Path) -> aiosqlite.Connection:
    """Create and return an asynchronous SQLite database connection."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db = await aiosqlite.connect(str(db_path))
    db.row_factory = aiosqlite.Row
    return db


async def init_database(db_path: Path) -> None:
    """Initialize database tables and indices if they do not exist."""
    logger.info(f"Initializing database at: {db_path}")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(str(db_path)) as db:
        await db.executescript(SCHEMA_SQL)
        await db.commit()
    logger.info("Database schema initialized successfully.")
