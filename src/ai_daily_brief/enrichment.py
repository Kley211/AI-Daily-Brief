"""Structured event enrichment with an offline MVP provider."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol

from .processing import EventCluster


@dataclass(frozen=True)
class EnrichedEvent:
    category: str
    summary: str
    why_it_matters: str
    importance: str
    confidence: str
    entities: tuple[str, ...]
    claims: tuple[str, ...]
    needs_review: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "category": self.category,
            "summary": self.summary,
            "why_it_matters": self.why_it_matters,
            "importance": self.importance,
            "confidence": self.confidence,
            "entities": list(self.entities),
            "claims": list(self.claims),
            "needs_review": self.needs_review,
        }


class Enricher(Protocol):
    def enrich(self, event: EventCluster) -> EnrichedEvent:
        """Convert an event cluster into a structured intelligence record."""


_CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "models": ("model", "llm", "gpt", "claude", "gemini", "foundation"),
    "products": ("launch", "release", "product", "feature", "api"),
    "opensource": ("open source", "github", "hugging face", "weights"),
    "infra": ("gpu", "cuda", "inference", "chip", "cloud", "nvidia"),
    "research": ("paper", "research", "benchmark", "arxiv"),
    "policy": ("policy", "regulation", "law", "copyright", "safety"),
    "community": ("reddit", "hacker news", "community"),
}
_ENTITY_RE = re.compile(r"\b(?:OpenAI|Anthropic|Google|Meta|Microsoft|NVIDIA|Hugging Face|LangChain|LlamaIndex|GPT[-\w]*|Claude[-\w]*|Gemini[-\w]*)\b", re.IGNORECASE)


def _category(text: str, source_id: str) -> str:
    lowered = text.lower()
    if source_id in {"reddit_localllama", "hackernews_ai"}:
        return "community"
    scores = {category: sum(keyword in lowered for keyword in keywords) for category, keywords in _CATEGORY_KEYWORDS.items()}
    return max(scores, key=scores.get) if max(scores.values()) else "products"


def _confidence(source_id: str, source_count: int) -> str:
    if source_id in {"reddit_localllama", "hackernews_ai"}:
        return "community"
    if source_count > 1:
        return "multi_source"
    return "official" if source_id in {"openai_blog", "anthropic_blog"} else "single_source"


class RuleBasedEnricher:
    """Deterministic fallback used before a model provider is configured."""

    def enrich(self, event: EventCluster) -> EnrichedEvent:
        item = event.canonical
        text = " ".join(filter(None, (item.title, item.content_excerpt))).strip()
        category = _category(text, item.source_id)
        confidence = _confidence(item.source_id, event.source_count)
        importance = "high" if event.source_count > 1 or category in {"models", "policy"} else "medium"
        entities = tuple(dict.fromkeys(match.group(0) for match in _ENTITY_RE.finditer(text)))
        return EnrichedEvent(
            category=category,
            summary=item.content_excerpt or item.title,
            why_it_matters="值得继续关注其对 AI 产品和开发者生态的影响。",
            importance=importance,
            confidence=confidence,
            entities=entities,
            claims=(item.title,),
            needs_review=confidence in {"community", "single_source"},
        )


def enrich_events(events: list[EventCluster], enricher: Enricher | None = None) -> list[EnrichedEvent]:
    provider = enricher or RuleBasedEnricher()
    return [provider.enrich(event) for event in events]


def validate_enrichment(value: EnrichedEvent) -> None:
    valid_categories = {"models", "products", "opensource", "infra", "research", "policy", "community"}
    valid_importance = {"high", "medium", "low"}
    valid_confidence = {"official", "multi_source", "single_source", "community", "unconfirmed"}
    if value.category not in valid_categories:
        raise ValueError("invalid enrichment category")
    if value.importance not in valid_importance:
        raise ValueError("invalid enrichment importance")
    if value.confidence not in valid_confidence:
        raise ValueError("invalid enrichment confidence")
    if not value.summary or not value.claims:
        raise ValueError("enrichment must include summary and claims")
