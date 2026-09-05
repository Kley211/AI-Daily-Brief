"""Stage 0 pipeline orchestration placeholders."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from .config import Settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RunResult:
    stage: str
    status: str = "planned"
    item_count: int = 0


def run_stage(stage: str, settings: Settings) -> RunResult:
    """Run a named stage and emit a stable log entry for the MVP skeleton."""
    valid_stages = {"fetch", "process", "digest"}
    if stage not in valid_stages:
        raise ValueError(f"unknown stage: {stage}")
    logger.info(
        "stage=%s status=planned timezone=%s lookback_hours=%s max_digest_items=%s",
        stage,
        settings.timezone,
        settings.lookback_hours,
        settings.max_digest_items,
    )
    return RunResult(stage=stage)


def run_pipeline(settings: Settings) -> list[RunResult]:
    """Run all stages in order; later stages will replace these placeholders."""
    return [run_stage(stage, settings) for stage in ("fetch", "process", "digest")]
