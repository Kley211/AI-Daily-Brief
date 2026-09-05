from datetime import datetime, timedelta, timezone

from ai_daily_brief.config import Settings
from ai_daily_brief.enrichment import RuleBasedEnricher
from ai_daily_brief.pipeline import build_daily_report
from ai_daily_brief.sources import RawItem


def test_build_daily_report_runs_full_in_memory_flow(monkeypatch):
    item = RawItem("openai_blog", "1", "OpenAI releases a GPT model", "https://example.com/1", None, "A model release.")
    monkeypatch.setattr("ai_daily_brief.pipeline.fetch_sources", lambda: [item])
    monkeypatch.setattr("ai_daily_brief.pipeline.enricher_from_env", lambda: RuleBasedEnricher())

    report = build_daily_report(Settings(max_digest_items=5))

    assert len(report.entries) == 1
    assert report.entries[0].enrichment.category == "models"


def test_build_daily_report_filters_old_items(monkeypatch):
    old = RawItem("openai_blog", "old", "Old model", "https://example.com/old", datetime.now(timezone.utc) - timedelta(days=2), "old")
    monkeypatch.setattr("ai_daily_brief.pipeline.fetch_sources", lambda: [old])
    monkeypatch.setattr("ai_daily_brief.pipeline.enricher_from_env", lambda: RuleBasedEnricher())

    report = build_daily_report(Settings(lookback_hours=1, max_digest_items=5))

    assert len(report.entries) == 0
