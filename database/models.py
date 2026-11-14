"""Database models and data transfer objects for Channel Analyzer."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
import json


@dataclass
class ChannelPost:
    """Represents a post from the Zero to Hero English Telegram channel."""
    message_id: int
    channel_id: int
    text: Optional[str]
    media_type: str = "text"
    topic: Optional[str] = None
    views: Optional[int] = None
    forwards: Optional[int] = None
    date: datetime = field(default_factory=datetime.utcnow)
    id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def clean_content(self) -> str:
        """Return clean readable content of the post."""
        content = self.text or ""
        return content.strip()


@dataclass
class PostComment:
    """Represents a user comment or question under a channel post."""
    message_id: int
    chat_id: int
    text: str
    reply_to_post_id: Optional[int] = None
    user_id: Optional[int] = None
    user_fullname: Optional[str] = None
    user_username: Optional[str] = None
    date: datetime = field(default_factory=datetime.utcnow)
    id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def clean_text(self) -> str:
        """Return sanitized comment text."""
        return self.text.strip()


@dataclass
class AnalysisRecord:
    """Represents an AI analysis result stored in database."""
    posts_analyzed_count: int
    comments_analyzed_count: int
    raw_topics_text: str
    topics_list: List[str]
    id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def topics_json(self) -> str:
        """Serialize topics list to JSON string."""
        return json.dumps(self.topics_list, ensure_ascii=False)

    @classmethod
    def from_row(cls, row: tuple) -> "AnalysisRecord":
        """Reconstruct AnalysisRecord from SQLite row."""
        # row: (id, created_at, posts_analyzed_count, comments_analyzed_count, raw_topics_text, topics_list_json)
        rec_id, dt_str, p_count, c_count, raw_text, json_str = row
        dt = datetime.fromisoformat(dt_str) if isinstance(dt_str, str) else dt_str
        try:
            t_list = json.loads(json_str) if json_str else []
        except Exception:
            t_list = []
        return cls(
            id=rec_id,
            created_at=dt,
            posts_analyzed_count=p_count,
            comments_analyzed_count=c_count,
            raw_topics_text=raw_text,
            topics_list=t_list
        )
