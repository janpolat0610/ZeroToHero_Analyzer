"""Gemini AI Analyzer module for Zero to Hero English Channel Analyzer."""

import asyncio
import logging
import re
from typing import List, Optional, Tuple

from analyzer.prompts import SYSTEM_INSTRUCTION, build_analysis_prompt
from database.models import ChannelPost, PostComment, AnalysisRecord

logger = logging.getLogger("ZeroToHeroAnalyzer.Analyzer")


class GeminiAnalyzer:
    """Handles communication with Google Gemini API to analyze channel content."""

    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        self.api_key = api_key.strip() if api_key else ""
        self.model_name = model_name or "gemini-2.5-flash"
        self._client = None
        self._init_client()

    def _init_client(self) -> None:
        """Initialize Google GenAI client."""
        if not self.api_key:
            logger.warning("Gemini API key is empty! AI analysis calls will fail until configured.")
            return

        try:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
            logger.info(f"Google GenAI client initialized with model: {self.model_name}")
        except Exception as e:
            logger.warning(f"Could not initialize google-genai client: {e}. Trying google-generativeai fallback...")
            try:
                import google.generativeai as genai_legacy
                genai_legacy.configure(api_key=self.api_key)
                self._client = "legacy"
                logger.info("Using google-generativeai fallback client.")
            except Exception as e2:
                logger.error(f"Failed to initialize any Gemini client: {e2}")

    def format_posts_for_prompt(self, posts: List[ChannelPost]) -> str:
        """Format posts list into clear text representation for the AI prompt."""
        if not posts:
            return "Oxirgi 2 kunda kanalga yangi postlar joylanmagan."

        lines = []
        for i, post in enumerate(posts, 1):
            date_str = post.date.strftime("%Y-%m-%d %H:%M") if post.date else "Noma'lum sana"
            views_str = f" | Ko'rishlar: {post.views}" if post.views else ""
            clean_text = post.clean_content.replace("\n", " ").strip()
            # Truncate overly long posts to avoid wasting token window
            if len(clean_text) > 400:
                clean_text = clean_text[:400] + "..."
            lines.append(f"{i}. [Post ID: #{post.message_id} | {date_str} | Turi: {post.media_type}{views_str}]\n   Matn: {clean_text}")

        return "\n\n".join(lines)

    def format_comments_for_prompt(self, comments: List[PostComment]) -> str:
        """Format comments list into clear text representation for the AI prompt."""
        if not comments:
            return "Oxirgi 2 kunda izohlar qoldirilmagan."

        lines = []
        for i, comment in enumerate(comments, 1):
            date_str = comment.date.strftime("%Y-%m-%d %H:%M") if comment.date else "Noma'lum sana"
            user_info = comment.user_fullname or comment.user_username or "Foydalanuvchi"
            clean_text = comment.clean_text.replace("\n", " ").strip()
            if len(clean_text) > 250:
                clean_text = clean_text[:250] + "..."
            reply_info = f" (Post #{comment.reply_to_post_id} ga javoban)" if comment.reply_to_post_id else ""
            lines.append(f"{i}. [{user_info} | {date_str}{reply_info}]: {clean_text}")

        return "\n".join(lines)

    def extract_topics_list(self, raw_text: str) -> List[str]:
        """Extract clean topic titles list from AI response text."""
        topics = []
        lines = raw_text.splitlines()
        for line in lines:
            line_str = line.strip()
            # Match lines starting with digits (e.g., '1. Topic', '1) Topic', '- Topic')
            match = re.match(r"^(?:\d+[\.\)]|\-|\*)\s*(.+)$", line_str)
            if match:
                topic_title = match.group(1).strip()
                # Clean bold or italic marks if present
                topic_title = re.sub(r"^[*_`]+|[*_`]+$", "", topic_title).strip()
                if topic_title and not topic_title.lower().startswith("zero to hero english"):
                    topics.append(topic_title)

        return topics

    def format_final_output(self, topics: List[str], raw_text: str) -> str:
        """Format topics list strictly to required specification."""
        header = "**Zero to Hero English — Tavsiya etilgan mavzular**\n"
        if not topics:
            # Fallback if regex parsing missed numbered lines
            cleaned_raw = raw_text.strip()
            if not cleaned_raw.startswith("**Zero to Hero English"):
                return f"{header}\n{cleaned_raw}"
            return cleaned_raw

        items = [f"{i}. {topic}" for i, topic in enumerate(topics, 1)]
        return f"{header}\n" + "\n".join(items)

    async def generate_topics(
        self,
        posts: List[ChannelPost],
        comments: List[PostComment]
    ) -> Tuple[str, List[str]]:
        """Call Gemini API and return formatted message and list of topics.

        Returns tuple of (formatted_output_text, list_of_topic_titles).
        """
        if not self.api_key:
            raise ValueError(
                "Gemini API kaliti kiritilmagan! Iltimos, .env faylida GEMINI_API_KEY ni to'g'ri sozlang."
            )

        posts_str = self.format_posts_for_prompt(posts)
        comments_str = self.format_comments_for_prompt(comments)
        user_prompt = build_analysis_prompt(posts_str, comments_str)

        logger.info(
            f"Sending analysis request to Gemini model '{self.model_name}' (Posts: {len(posts)}, Comments: {len(comments)})..."
        )

        response_text = ""
        max_retries = 3
        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                if self._client != "legacy" and self._client is not None:
                    # Modern google-genai SDK
                    from google.genai import types

                    config = types.GenerateContentConfig(
                        system_instruction=SYSTEM_INSTRUCTION,
                        temperature=0.7,
                        max_output_tokens=1000,
                    )
                    # Run async generation
                    response = await self._client.aio.models.generate_content(
                        model=self.model_name,
                        contents=user_prompt,
                        config=config
                    )
                    response_text = response.text or ""
                else:
                    # Legacy google-generativeai fallback
                    import google.generativeai as genai_legacy
                    model = genai_legacy.GenerativeModel(
                        model_name=self.model_name,
                        system_instruction=SYSTEM_INSTRUCTION
                    )
                    res = await model.generate_content_async(user_prompt)
                    response_text = res.text or ""

                if response_text.strip():
                    break

            except Exception as e:
                last_error = e
                logger.warning(f"Gemini API attempt {attempt} failed: {e}")
                if attempt < max_retries:
                    await asyncio.sleep(2 * attempt)
                else:
                    logger.error(f"All {max_retries} attempts failed: {e}", exc_info=True)
                    raise RuntimeError(f"Gemini API bilan bog'lanishda xatolik yuz berdi: {e}") from last_error

        topics_list = self.extract_topics_list(response_text)
        final_message = self.format_final_output(topics_list, response_text)
        logger.info(f"Gemini AI successfully returned {len(topics_list)} topics.")
        return final_message, topics_list
