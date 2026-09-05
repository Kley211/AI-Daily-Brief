"""Adapters for community sources with JSON and RSS endpoints."""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Callable

from .base import RawItem
from .rss import load_feed


def fetch_json(url: str, timeout: int = 20) -> dict:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "ai-daily-brief/0.1 (+public-feed-reader)"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read())


class _RssAdapter:
    source_id: str
    default_url: str

    def __init__(self, feed_url: str | None = None) -> None:
        self.feed_url = feed_url or os.getenv(
            f"AI_BRIEF_{self.source_id.upper()}_FEED_URL", self.default_url
        )

    def fetch(self) -> list[RawItem]:
        return load_feed(self.feed_url, self.source_id)


class HuggingFaceAdapter(_RssAdapter):
    source_id = "huggingface"
    default_url = "https://huggingface.co/blog/feed.xml"


class LangChainAdapter(_RssAdapter):
    source_id = "langchain"
    default_url = "https://blog.langchain.dev/rss/"


class LlamaIndexAdapter(_RssAdapter):
    source_id = "llamaindex"
    default_url = "https://www.llamaindex.ai/blog/rss.xml"


class RedditLocalLlamaAdapter(_RssAdapter):
    source_id = "reddit_localllama"
    default_url = "https://www.reddit.com/r/LocalLLaMA/.rss"


class HackerNewsAIAdapter:
    source_id = "hackernews_ai"
    default_url = "https://hn.algolia.com/api/v1/search_by_date"
    keywords = (
        "ai", "llm", "gpt", "claude", "gemini", "agent", "rag", "inference",
        "gpu", "cuda", "open source model", "machine learning",
    )

    def __init__(
        self,
        api_url: str | None = None,
        loader: Callable[[str], dict] = fetch_json,
    ) -> None:
        self.api_url = api_url or os.getenv(
            "AI_BRIEF_HACKERNEWS_AI_API_URL", self.default_url
        )
        self.loader = loader

    def fetch(self) -> list[RawItem]:
        query = urllib.parse.urlencode({"query": "AI", "tags": "story"})
        payload = self.loader(f"{self.api_url}?{query}")
        items: list[RawItem] = []
        for hit in payload.get("hits", []):
            title = (hit.get("title") or "").strip()
            url = (hit.get("url") or "").strip()
            text = " ".join((hit.get("story_text") or "").split())
            searchable = f"{title} {text}".lower()
            if not title or not url or not any(word in searchable for word in self.keywords):
                continue
            created = hit.get("created_at")
            published_at = None
            if created:
                try:
                    published_at = datetime.fromisoformat(created.replace("Z", "+00:00"))
                except ValueError:
                    published_at = None
            items.append(
                RawItem(
                    source_id=self.source_id,
                    external_id=str(hit.get("objectID") or url),
                    title=title,
                    url=url,
                    published_at=published_at or datetime.now(timezone.utc),
                    content_excerpt=text,
                    author=hit.get("author") or "",
                    metadata={"points": str(hit.get("points") or 0)},
                )
            )
        return items
