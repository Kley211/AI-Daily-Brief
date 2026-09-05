"""Pipeline orchestration for source fetching and later processing stages."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from .config import Settings
from .sources import AnthropicBlogAdapter, OpenAIBlogAdapter, RawItem

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RunResult:
    stage: str
    status: str = "planned"
    item_count: int = 0


def fetch_sources() -> list[RawItem]:
    """Fetch the official sources currently implemented in the MVP."""
    items: list[RawItem] = []
    for adapter in (OpenAIBlogAdapter(), AnthropicBlogAdapter()):
        try:
            fetched = adapter.fetch()
        except Exception:
            logger.exception("source=%s status=failed", adapter.source_id)
            continue
        logger.info("source=%s status=ok item_count=%s", adapter.source_id, len(fetched))
        items.extend(fetched)
    return items


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
    """Run all stages in order; later stages will replace these placeholders."""
    return [run_stage(stage, settings) for stage in ("fetch", "process", "digest")]
