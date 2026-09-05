import json

from ai_daily_brief.enrichment import OpenAICompatibleEnricher
from ai_daily_brief.enrichment import enricher_from_env
from ai_daily_brief.processing import EventCluster
from ai_daily_brief.sources import RawItem


def test_openai_compatible_provider_parses_structured_response(monkeypatch):
    item = RawItem("openai_blog", "1", "OpenAI model release", "https://example.com", None, "A release")
    event = EventCluster(item, (item,))
    response = {
        "choices": [{"message": {"content": json.dumps({
            "category": "models",
            "summary": "A model release",
            "why_it_matters": "It may affect developers.",
            "importance": "high",
            "confidence": "official",
            "entities": ["OpenAI"],
            "claims": ["OpenAI model release"],
            "needs_review": False,
        })}}]
    }

    class FakeResponse:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def read(self):
            return json.dumps(response).encode()

    monkeypatch.setattr("urllib.request.urlopen", lambda *args, **kwargs: FakeResponse())
    result = OpenAICompatibleEnricher("https://example.test", "key", "test-model").enrich(event)

    assert result.category == "models"
    assert result.entities == ("OpenAI",)


def test_deepseek_defaults_to_built_in_endpoint(monkeypatch):
    monkeypatch.setenv("AI_BRIEF_MODEL_API_KEY", "test-key")
    monkeypatch.setenv("AI_BRIEF_MODEL_NAME", "")
    monkeypatch.delenv("AI_BRIEF_MODEL_PROVIDER", raising=False)
    monkeypatch.delenv("AI_BRIEF_MODEL_ENDPOINT", raising=False)

    provider = enricher_from_env()

    assert isinstance(provider, OpenAICompatibleEnricher)
    assert provider.endpoint == "https://api.deepseek.com/chat/completions"
    assert provider.model == "deepseek-chat"
