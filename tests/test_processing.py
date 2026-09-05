from datetime import datetime, timezone

from ai_daily_brief.processing import (
    cluster_events,
    content_hash,
    deduplicate_items,
    normalize_url,
    title_similarity,
)
from ai_daily_brief.sources import RawItem


def item(title: str, url: str, source: str = "a") -> RawItem:
    return RawItem(
        source_id=source,
        external_id=url,
        title=title,
        url=url,
        published_at=datetime(2026, 9, 5, tzinfo=timezone.utc),
        content_excerpt="summary",
    )


def test_normalize_url_removes_tracking_parameters():
    assert normalize_url("HTTPS://Example.COM/post/?utm_source=x&id=1#part") == "https://example.com/post?id=1"


def test_deduplicate_items_collapses_url_and_similar_titles():
    items = [
        item("OpenAI releases a new model", "https://example.com/a?utm_source=x"),
        item("OpenAI releases a new model", "https://example.com/a"),
        item("OpenAI releases new model", "https://other.example.com/b", "b"),
    ]

    unique = deduplicate_items(items)

    assert len(unique) == 1
    assert content_hash(unique[0])
    assert title_similarity(items[0].title, items[2].title) >= 0.82


def test_cluster_events_retains_related_sources():
    items = [
        item("Anthropic launches a new model", "https://a.example/1", "a"),
        item("Anthropic launches new model", "https://b.example/2", "b"),
        item("A separate GPU benchmark", "https://c.example/3", "c"),
    ]

    clusters = cluster_events(items)

    assert len(clusters) == 2
    assert clusters[0].source_count == 2
    assert len(clusters[0].related) == 2
