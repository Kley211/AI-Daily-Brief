"""Adapters for the first two official blog sources."""

from __future__ import annotations

import os

from .base import RawItem
from .html import load_listing
from .rss import load_feed


class _OfficialBlogAdapter:
    source_id: str
    default_url: str

    def __init__(self, feed_url: str | None = None) -> None:
        self.feed_url = feed_url or os.getenv(
            f"AI_BRIEF_{self.source_id.upper()}_FEED_URL", self.default_url
        )

    def fetch(self) -> list[RawItem]:
        return load_feed(self.feed_url, self.source_id)


class OpenAIBlogAdapter(_OfficialBlogAdapter):
    source_id = "openai_blog"
    default_url = "https://openai.com/blog/rss.xml"


class AnthropicBlogAdapter(_OfficialBlogAdapter):
    source_id = "anthropic_blog"
    default_url = "https://www.anthropic.com/news"

    def fetch(self) -> list[RawItem]:
        return load_listing(self.feed_url, self.source_id, r"/news/")
