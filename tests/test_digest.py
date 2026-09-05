from datetime import datetime, timezone

from ai_daily_brief.digest import build_report, render_html, render_text
from ai_daily_brief.enrichment import RuleBasedEnricher
from ai_daily_brief.processing import EventCluster
from ai_daily_brief.sources import RawItem


def make_event(title="OpenAI releases a GPT model"):
    item = RawItem("openai_blog", "1", title, "https://example.com/a", datetime.now(timezone.utc), "A model release.")
    return EventCluster(item, (item,))


def test_build_report_and_render_both_formats():
    event = make_event()
    report = build_report([event], [RuleBasedEnricher().enrich(event)])
    text, markup = render_text(report), render_html(report)
    assert "今日结论" in text
    assert "OpenAI releases" in text
    assert "<!doctype html>" in markup
    assert "查看原文" in markup


def test_empty_report_is_readable():
    report = build_report([], [])
    assert "暂无重点消息" in render_text(report)
    assert "暂无重点消息" in render_html(report)
