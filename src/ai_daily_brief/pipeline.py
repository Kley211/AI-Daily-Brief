"""Pipeline orchestration for source fetching and later processing stages."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from .config import Settings
from .digest import DigestReport, build_report
from .enrichment import enrich_events, enricher_from_env, validate_enrichment
from .processing import cluster_events, deduplicate_items
from .sources import (
    AnthropicBlogAdapter,
    HackerNewsAIAdapter,
    HuggingFaceAdapter,
    LangChainAdapter,
    LlamaIndexAdapter,
    OpenAIBlogAdapter,
    RawItem,
    RedditLocalLlamaAdapter,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RunResult:
    stage: str
    status: str = "planned"
    item_count: int = 0


def fetch_sources() -> list[RawItem]:
    """Fetch the official sources currently implemented in the MVP."""
    items: list[RawItem] = []
    adapters = (
        OpenAIBlogAdapter(),
        AnthropicBlogAdapter(),
        HuggingFaceAdapter(),
        LangChainAdapter(),
        LlamaIndexAdapter(),
        RedditLocalLlamaAdapter(),
        HackerNewsAIAdapter(),
    )
    for adapter in adapters:
        try:
            fetched = adapter.fetch()
        except Exception:
            logger.exception("source=%s status=failed", adapter.source_id)
            continue
        logger.info("source=%s status=ok item_count=%s", adapter.source_id, len(fetched))
        items.extend(fetched)
    return items


def build_daily_report(settings: Settings) -> DigestReport:
    """Run fetching and processing, returning a report ready to render or send."""
    raw_items = fetch_sources()
    unique_items = deduplicate_items(raw_items)
    events = cluster_events(unique_items)
    enriched = enrich_events(events, enricher_from_env())
    for value in enriched:
        validate_enrichment(value)
    logger.info(
        "stage=process status=completed raw_count=%s unique_count=%s event_count=%s enriched_count=%s",
        len(raw_items), len(unique_items), len(events), len(enriched),
    )
    return build_report(events, enriched, settings.max_digest_items)


def run_stage(stage: str, settings: Settings) -> RunResult:
    """Run a named pipeline stage."""
    valid_stages = {"fetch", "process", "digest"}
    if stage not in valid_stages:
        raise ValueError(f"unknown stage: {stage}")
    if stage == "fetch":
        items = fetch_sources()
        return RunResult(stage=stage, status="completed", item_count=len(items))
    logger.info(
        "stage=%s status=planned timezone=%s lookback_hours=%s max_digest_items=%s",
        stage, settings.timezone, settings.lookback_hours, settings.max_digest_items
    )
    return RunResult(stage=stage)


def run_pipeline(settings: Settings) -> list[RunResult]:
    """Run the in-memory MVP pipeline in stage order."""
    report = build_daily_report(settings)
    return [
        RunResult(stage="fetch", status="completed"),
        RunResult(stage="process", status="completed", item_count=len(report.entries)),
        RunResult(stage="digest", status="completed", item_count=len(report.entries)),
    ]
