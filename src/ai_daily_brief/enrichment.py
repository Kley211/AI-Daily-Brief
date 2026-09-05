"""Structured event enrichment with an offline MVP provider."""

from __future__ import annotations

import re
import json
import os
import urllib.request
from dataclasses import dataclass
from typing import Protocol

from .processing import EventCluster
from .config import load_dotenv
from .tls import default_context


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


class OpenAICompatibleEnricher:
    """LLM provider for DeepSeek, Qwen, and compatible chat APIs."""

    def __init__(
        self,
        endpoint: str,
        api_key: str,
        model: str,
        timeout: int = 60,
    ) -> None:
        self.endpoint = endpoint
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def enrich(self, event: EventCluster) -> EnrichedEvent:
        item = event.canonical
        prompt = {
            "title": item.title,
            "excerpt": item.content_excerpt,
            "source": item.source_id,
            "source_count": event.source_count,
        }
        schema = (
            "Return JSON only with keys: category (models|products|opensource|infra|research|policy|community), "
            "summary, why_it_matters, importance (high|medium|low), confidence "
            "(official|multi_source|single_source|community|unconfirmed), entities (array), "
            "claims (array), needs_review (boolean). Do not invent facts."
        )
        payload = {
            "model": self.model,
            "temperature": 0.1,
            "messages": [
                {"role": "system", "content": "You are a careful AI news analyst. " + schema},
                {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
            ],
        }
        request = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "ai-daily-brief/0.1",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout, context=default_context()) as response:
            body = json.loads(response.read())
        content = body["choices"][0]["message"]["content"]
        content = content.strip().removeprefix("```json").removesuffix("```").strip()
        value = json.loads(content)
        result = EnrichedEvent(
            category=value["category"],
            summary=value["summary"],
            why_it_matters=value["why_it_matters"],
            importance=value["importance"],
            confidence=value["confidence"],
            entities=tuple(value.get("entities", [])),
            claims=tuple(value.get("claims", [])),
            needs_review=bool(value.get("needs_review", False)),
        )
        validate_enrichment(result)
        return result


def enricher_from_env() -> Enricher:
    """Select a configured LLM, falling back safely to offline mode."""
    load_dotenv()
    api_key = os.getenv("AI_BRIEF_MODEL_API_KEY", "")
    provider = os.getenv("AI_BRIEF_MODEL_PROVIDER", "deepseek" if api_key else "rule_based").lower()
    if provider == "deepseek" and api_key:
        return OpenAICompatibleEnricher(
            endpoint=os.getenv("AI_BRIEF_MODEL_ENDPOINT") or "https://api.deepseek.com/chat/completions",
            api_key=api_key,
            model=os.getenv("AI_BRIEF_MODEL_NAME") or "deepseek-chat",
        )
    if provider == "qwen" and api_key:
        return OpenAICompatibleEnricher(
            endpoint=os.getenv(
                "AI_BRIEF_MODEL_ENDPOINT"
            ) or "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
            api_key=api_key,
            model=os.getenv("AI_BRIEF_MODEL_NAME") or "qwen-plus",
        )
    return RuleBasedEnricher()


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
