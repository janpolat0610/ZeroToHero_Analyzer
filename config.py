"""Configuration module for Zero to Hero English Channel Analyzer Bot.

Loads configuration from .env and ensures all data paths are strictly placed on D: drive.
"""

from pathlib import Path
from typing import List, Optional, Union
import logging
import os
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base project directory strictly on D: drive
BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    """Application settings schema with validation."""

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Telegram Bot Token
    BOT_TOKEN: str = Field(..., description="Standalone Telegram Bot Token")

    # Google Gemini API
    GEMINI_API_KEY: str = Field(..., description="Google Gemini API Key")
    GEMINI_MODEL: str = Field(default="gemini-2.5-flash", description="Gemini model name")

    # Admins
    ADMIN_IDS: List[int] = Field(default_factory=list, description="List of Telegram admin IDs")

    # Channel & Discussion Group
    CHANNEL_ID: Optional[Union[int, str]] = Field(default=None, description="Telegram Channel ID or @username")
    DISCUSSION_GROUP_ID: Optional[Union[int, str]] = Field(default=None, description="Linked Discussion Group ID or @username")

    # Storage paths (Defaulting strictly to D: drive)
    DATABASE_PATH: Path = Field(
        default=BASE_DIR / "database" / "analyzer.db",
        description="Path to SQLite database file"
    )
    LOG_FILE_PATH: Path = Field(
        default=BASE_DIR / "logs" / "bot.log",
        description="Path to application log file"
    )
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")

    # Cleanup schedule (in hours)
    CLEANUP_INTERVAL_HOURS: int = Field(default=1, description="Interval for 2-day data auto-cleanup")

    @field_validator("ADMIN_IDS", mode="before")
    @classmethod
    def parse_admin_ids(cls, v: Union[str, int, List[Union[str, int]]]) -> List[int]:
        """Parse comma-separated admin IDs from environment variable."""
        if isinstance(v, (int, float)):
            return [int(v)]
        if isinstance(v, str):
            ids = []
            for item in v.split(","):
                cleaned = item.strip()
                if cleaned.isdigit() or (cleaned.startswith("-") and cleaned[1:].isdigit()):
                    ids.append(int(cleaned))
            return ids
        if isinstance(v, list):
            return [int(x) for x in v if str(x).lstrip("-").isdigit()]
        return []

    @field_validator("DATABASE_PATH", "LOG_FILE_PATH", mode="before")
    @classmethod
    def resolve_storage_path(cls, v: Union[str, Path, None], info) -> Path:
        """Resolve paths cross-platform (handles Windows drive letters gracefully on Linux/Docker)."""
        field_name = info.field_name
        default_subpath = "database/analyzer.db" if field_name == "DATABASE_PATH" else "logs/bot.log"
        if not v:
            return BASE_DIR / default_subpath

        p_str = str(v).strip()
        # If running on Linux/Docker and path contains Windows drive (e.g. D:\ZeroToHero_Analyzer\...)
        if os.name != "nt" and len(p_str) >= 2 and p_str[1] == ":":
            # Extract relative portion after drive letter and folder
            clean_rel = p_str[3:].replace("\\", "/").lstrip("/")
            if "database" in clean_rel:
                return BASE_DIR / "database" / "analyzer.db"
            elif "logs" in clean_rel:
                return BASE_DIR / "logs" / "bot.log"
            return BASE_DIR / clean_rel

        path = Path(p_str)
        if not path.is_absolute():
            return BASE_DIR / path
        return path

    def is_admin(self, user_id: int) -> bool:
        """Check if a Telegram user ID is an administrator."""
        return user_id in self.ADMIN_IDS


def setup_logging(settings: Settings) -> logging.Logger:
    """Configure system logging to both D: drive file and console."""
    settings.LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    settings.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    numeric_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # File handler on D: drive
    file_handler = logging.FileHandler(
        filename=str(settings.LOG_FILE_PATH),
        encoding="utf-8",
        mode="a"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(numeric_level)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(numeric_level)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    # Remove existing handlers to avoid duplicate logs
    root_logger.handlers.clear()
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Suppress excessive logging from libraries
    logging.getLogger("aiogram").setLevel(logging.INFO)
    logging.getLogger("aiosqlite").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.INFO)

    logger = logging.getLogger("ZeroToHeroAnalyzer")
    logger.info(f"Logging initialized. Log file: {settings.LOG_FILE_PATH}")
    return logger


# Instantiate settings helper
def load_config() -> Settings:
    """Load settings from .env file or environment variables."""
    return Settings()
