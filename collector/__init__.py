"""Collector routers for Zero to Hero English Channel Analyzer."""

from collector.channel_collector import router as channel_router
from collector.comment_collector import router as comment_router
from collector.manual_importer import router as importer_router

__all__ = ["channel_router", "comment_router", "importer_router"]
