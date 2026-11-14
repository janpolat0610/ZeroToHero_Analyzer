"""Comprehensive verification and sanity test script for Zero to Hero Analyzer Bot."""

import asyncio
import os
import sys

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import Settings
from database.db import init_database
from database.models import ChannelPost, PostComment, AnalysisRecord
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
from analyzer.gemini_analyzer import GeminiAnalyzer


async def run_tests():
    print("==================================================")
    print("STARTING ZERO TO HERO ANALYZER SYSTEM TESTS")
    print("==================================================")

    test_db_path = Path("D:/ZeroToHero_Analyzer/database/test_analyzer.db")
    if test_db_path.exists():
        test_db_path.unlink()

    # Test 1: Database Initialization
    print("\n[Test 1] Testing Database Schema Initialization...")
    await init_database(test_db_path)
    assert test_db_path.exists(), "Database file was not created!"
    print("✅ Database created and tables initialized successfully.")

    # Test 2: Inserting Channel Posts (Recent vs Old)
    print("\n[Test 2] Testing Channel Posts Storage and 2-Day Filtering...")
    now = datetime.now(timezone.utc)
    one_day_ago = now - timedelta(days=1)
    three_days_ago = now - timedelta(days=3)

    recent_post = ChannelPost(
        message_id=101,
        channel_id=-1001234567890,
        text="Bugun ingliz tilida Present Continuous zamoni va uning istisno holatlarini o'rganamiz: State verbs.",
        media_type="text",
        views=450,
        forwards=12,
        date=one_day_ago
    )
    old_post = ChannelPost(
        message_id=100,
        channel_id=-1001234567890,
        text="Eski dars: To be fe'li va uning Present Simple da qo'llanishi.",
        media_type="text",
        views=320,
        forwards=5,
        date=three_days_ago
    )

    await save_post(test_db_path, recent_post)
    await save_post(test_db_path, old_post)

    recent_posts = await get_recent_posts(test_db_path, days=2)
    assert len(recent_posts) == 1, f"Expected 1 recent post within 2 days, got {len(recent_posts)}"
    assert recent_posts[0].message_id == 101, f"Expected message_id 101, got {recent_posts[0].message_id}"
    print(f"✅ Filter correctly retrieved {len(recent_posts)} post(s) within 2 days (excluded 3-day old post).")

    # Test 3: Deduplication
    print("\n[Test 3] Testing Post Deduplication (ON CONFLICT UPDATE)...")
    updated_post = ChannelPost(
        message_id=101,
        channel_id=-1001234567890,
        text="Yangilangan: Bugun Present Continuous zamoni.",
        media_type="text",
        views=600,
        date=one_day_ago
    )
    await save_post(test_db_path, updated_post)
    recent_posts_after_dup = await get_recent_posts(test_db_path, days=2)
    assert len(recent_posts_after_dup) == 1, f"Expected 1 post after update, got {len(recent_posts_after_dup)}"
    assert recent_posts_after_dup[0].views == 600, "Views was not updated!"
    print("✅ Deduplication and update verified successfully.")

    # Test 4: Inserting Comments
    print("\n[Test 4] Testing Comments Storage and Filtering...")
    comment1 = PostComment(
        message_id=501,
        chat_id=-1009876543210,
        reply_to_post_id=101,
        text="Ustoz, 'hear' va 'listen' so'zlarining farqini ham tushuntirib bering iltimos!",
        user_id=111222,
        user_fullname="Ali Valiyev",
        date=one_day_ago
    )
    comment2 = PostComment(
        message_id=502,
        chat_id=-1009876543210,
        reply_to_post_id=101,
        text="Phrasal verbs bo'yicha ham post qilinglar, ayniqsa 'look' bilan keladiganlari.",
        user_id=333444,
        user_fullname="Madina",
        date=now - timedelta(hours=5)
    )
    old_comment = PostComment(
        message_id=500,
        chat_id=-1009876543210,
        reply_to_post_id=100,
        text="Rahmat!",
        user_id=555666,
        user_fullname="Eski foydalanuvchi",
        date=three_days_ago
    )

    await save_comment(test_db_path, comment1)
    await save_comment(test_db_path, comment2)
    await save_comment(test_db_path, old_comment)

    recent_comments = await get_recent_comments(test_db_path, days=2)
    assert len(recent_comments) == 2, f"Expected 2 recent comments within 2 days, got {len(recent_comments)}"
    print(f"✅ Filter correctly retrieved {len(recent_comments)} recent comments (excluded 3-day old comment).")

    # Test 5: 2-Day Auto-Cleanup Job
    print("\n[Test 5] Testing 2-Day Auto-Cleanup Job...")
    del_posts, del_comments = await cleanup_old_data(test_db_path, days=2)
    assert del_posts == 1, f"Expected 1 old post deleted, got {del_posts}"
    assert del_comments == 1, f"Expected 1 old comment deleted, got {del_comments}"

    stats = await get_db_stats(test_db_path, days=2)
    assert stats["total_posts_count"] == 1, f"Expected 1 total post remaining, got {stats['total_posts_count']}"
    assert stats["total_comments_count"] == 2, f"Expected 2 total comments remaining, got {stats['total_comments_count']}"
    print(f"✅ Auto-cleanup successfully purged {del_posts} post and {del_comments} comment older than 2 days.")

    # Test 6: AI Analyzer Prompt Formatting and Output Parsing
    print("\n[Test 6] Testing Gemini Analyzer Prompt Formatter & Output Parser...")
    analyzer = GeminiAnalyzer(api_key="", model_name="gemini-2.5-flash")

    formatted_posts = analyzer.format_posts_for_prompt(recent_posts)
    formatted_comments = analyzer.format_comments_for_prompt(recent_comments)

    assert "Present Continuous" in formatted_posts
    assert "Ali Valiyev" in formatted_comments
    assert "hear" in formatted_comments

    # Test parser with mock AI response
    mock_ai_output = """
**Zero to Hero English — Tavsiya etilgan mavzular**

1. Hear vs Listen: Farqlari va to'g'ri ishlatish qoidalari
2. "Look" fe'li bilan eng muhim 10 ta Phrasal Verb (Look for, Look after, Look up)
3. State Verbs (Holat fe'llari) va ularni Continuous zamonlarda ishlatmaslik sirlari
4. Kundalik hayotda eng ko'p adashtiriladigan 5 ta inglizcha so'z
5. How to start speaking English from Zero: Boshlang'ich iboralar
"""
    topics_list = analyzer.extract_topics_list(mock_ai_output)
    assert len(topics_list) == 5, f"Expected 5 parsed topics, got {len(topics_list)}"
    assert "Hear vs Listen" in topics_list[0]
    assert "Look" in topics_list[1]
    final_output = analyzer.format_final_output(topics_list, mock_ai_output)
    assert final_output.startswith("**Zero to Hero English — Tavsiya etilgan mavzular**")
    print("✅ Prompt formatting and topic extraction validated perfectly.")

    # Test 7: Analysis History Storage
    print("\n[Test 7] Testing Analysis Record Storage and Retrieval...")
    analysis_rec = AnalysisRecord(
        posts_analyzed_count=1,
        comments_analyzed_count=2,
        raw_topics_text=final_output,
        topics_list=topics_list
    )
    rec_id = await save_analysis(test_db_path, analysis_rec)
    assert rec_id > 0, "Failed to save analysis record"

    latest_rec = await get_latest_analysis(test_db_path)
    assert latest_rec is not None, "Failed to fetch latest analysis record"
    assert len(latest_rec.topics_list) == 5
    assert latest_rec.posts_analyzed_count == 1
    assert latest_rec.comments_analyzed_count == 2
    print("✅ Analysis record saved and retrieved successfully.")

    # Clean up test database
    if test_db_path.exists():
        test_db_path.unlink()

    print("\n==================================================")
    print("ALL TESTS PASSED SUCCESSFULLY! (7/7)")
    print("==================================================")


if __name__ == "__main__":
    asyncio.run(run_tests())
