import json

from ai_daily_brief.enrichment import OpenAICompatibleEnricher
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
