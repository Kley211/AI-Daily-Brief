from datetime import datetime, timezone

from ai_daily_brief.enrichment import EnrichedEvent, RuleBasedEnricher, enrich_events, validate_enrichment
from ai_daily_brief.processing import EventCluster
from ai_daily_brief.sources import RawItem


def event(source_id="openai_blog", title="OpenAI releases a new GPT model"):
    item = RawItem(
        source_id=source_id,
        external_id="1",
        title=title,
        url="https://example.com/1",
        published_at=datetime.now(timezone.utc),
        content_excerpt="A new model release for developers.",
    )
    return EventCluster(canonical=item, related=(item,))


def test_rule_based_enricher_returns_valid_structured_output():
    result = RuleBasedEnricher().enrich(event())
    validate_enrichment(result)
    assert result.category == "models"
    assert result.confidence == "official"
    assert "OpenAI" in result.entities
    assert result.claims


def test_community_event_requires_review():
    result = enrich_events([event("reddit_localllama", "New open source model weights")])[0]
    assert result.category == "community"
    assert result.confidence == "community"
    assert result.needs_review is True


def test_invalid_enrichment_is_rejected():
    result = RuleBasedEnricher().enrich(event())
    invalid = EnrichedEvent(
        category="invalid",
        summary=result.summary,
        why_it_matters=result.why_it_matters,
        importance=result.importance,
        confidence=result.confidence,
        entities=result.entities,
        claims=result.claims,
    )
    try:
        validate_enrichment(invalid)
    except ValueError as exc:
        assert "category" in str(exc)
    else:
        raise AssertionError("invalid enrichment should fail validation")
