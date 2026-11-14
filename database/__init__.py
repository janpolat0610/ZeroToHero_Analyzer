"""Database module for Zero to Hero English Channel Analyzer."""

from database.models import ChannelPost, PostComment, AnalysisRecord
from database.db import init_database, get_db_connection
from database.crud import (
    save_post,
    save_comment,
    get_recent_posts,
    get_recent_comments,
    cleanup_old_data,
    save_analysis,
    get_latest_analysis,
    get_db_stats,
)

__all__ = [
    "ChannelPost",
    "PostComment",
    "AnalysisRecord",
    "init_database",
    "get_db_connection",
    "save_post",
    "save_comment",
    "get_recent_posts",
    "get_recent_comments",
    "cleanup_old_data",
    "save_analysis",
    "get_latest_analysis",
    "get_db_stats",
]
