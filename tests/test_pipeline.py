import pytest

from ai_daily_brief.config import Settings
import ai_daily_brief.pipeline as pipeline
from ai_daily_brief.pipeline import run_pipeline, run_stage


def test_pipeline_runs_stages_in_order(monkeypatch):
    monkeypatch.setattr(pipeline, "fetch_sources", lambda: [])
    results = run_pipeline(Settings())

    assert [result.stage for result in results] == ["fetch", "process", "digest"]
    assert results[0].status == "completed"
    assert all(result.status == "planned" for result in results[1:])


def test_unknown_stage_is_rejected():
    with pytest.raises(ValueError, match="unknown stage"):
        run_stage("unknown", Settings())
