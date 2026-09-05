from ai_daily_brief.sources.community import HackerNewsAIAdapter


def test_hackernews_adapter_filters_and_normalizes_hits():
    payload = {
        "hits": [
            {
                "objectID": "1",
                "title": "A new open source LLM",
                "url": "https://example.com/llm",
                "story_text": "Model release",
                "created_at": "2026-09-05T00:00:00.000Z",
                "author": "alice",
                "points": 42,
            },
            {
                "objectID": "2",
                "title": "Unrelated database tips",
                "url": "https://example.com/db",
            },
        ]
    }

    adapter = HackerNewsAIAdapter(
        api_url="https://example.test/search", loader=lambda url: payload
    )

    items = adapter.fetch()

    assert len(items) == 1
    assert items[0].source_id == "hackernews_ai"
    assert items[0].external_id == "1"
    assert items[0].metadata["points"] == "42"
