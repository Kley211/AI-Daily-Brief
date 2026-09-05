import pytest

from ai_daily_brief.config import Settings
from ai_daily_brief.pipeline import run_pipeline, run_stage


def test_pipeline_runs_stages_in_order():
    results = run_pipeline(Settings())

    assert [result.stage for result in results] == ["fetch", "process", "digest"]
    assert all(result.status == "planned" for result in results)


def test_unknown_stage_is_rejected():
    with pytest.raises(ValueError, match="unknown stage"):
        run_stage("unknown", Settings())
