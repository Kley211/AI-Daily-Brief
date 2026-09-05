from ai_daily_brief import pipeline


def test_fetch_sources_retries_failed_adapter(monkeypatch):
    class Adapter:
        source_id = "test"
        calls = 0

        def fetch(self):
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError("temporary")
            return []

    adapter = Adapter()
    monkeypatch.setattr(pipeline, "OpenAIBlogAdapter", lambda: adapter)
    monkeypatch.setattr(pipeline, "AnthropicBlogAdapter", lambda: adapter)
    monkeypatch.setattr(pipeline, "HuggingFaceAdapter", lambda: adapter)
    monkeypatch.setattr(pipeline, "LangChainAdapter", lambda: adapter)
    monkeypatch.setattr(pipeline, "LlamaIndexAdapter", lambda: adapter)
    monkeypatch.setattr(pipeline, "RedditLocalLlamaAdapter", lambda: adapter)
    monkeypatch.setattr(pipeline, "HackerNewsAIAdapter", lambda: adapter)
    monkeypatch.setenv("AI_BRIEF_SOURCE_RETRIES", "1")
    monkeypatch.setattr(pipeline.time, "sleep", lambda _: None)

    assert pipeline.fetch_sources() == []
    assert adapter.calls == 8
