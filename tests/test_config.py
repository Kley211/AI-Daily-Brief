import pytest

from ai_daily_brief.config import Settings


def test_settings_use_defaults(monkeypatch):
    for name in (
        "AI_BRIEF_TIMEZONE",
        "AI_BRIEF_SEND_TIME",
        "AI_BRIEF_LOOKBACK_HOURS",
        "AI_BRIEF_MAX_DIGEST_ITEMS",
        "AI_BRIEF_RECIPIENT",
    ):
        monkeypatch.delenv(name, raising=False)

    settings = Settings.from_env()

    assert settings.timezone == "Asia/Shanghai"
    assert settings.send_time == "08:00"
    assert settings.lookback_hours == 24
    assert settings.max_digest_items == 10
    assert settings.recipient == ""


def test_settings_read_environment(monkeypatch):
    monkeypatch.setenv("AI_BRIEF_TIMEZONE", "UTC")
    monkeypatch.setenv("AI_BRIEF_LOOKBACK_HOURS", "12")
    monkeypatch.setenv("AI_BRIEF_MAX_DIGEST_ITEMS", "5")

    settings = Settings.from_env()

    assert settings.timezone == "UTC"
    assert settings.lookback_hours == 12
    assert settings.max_digest_items == 5


def test_settings_reject_invalid_integer(monkeypatch):
    monkeypatch.setenv("AI_BRIEF_LOOKBACK_HOURS", "nope")

    with pytest.raises(ValueError, match="AI_BRIEF_LOOKBACK_HOURS"):
        Settings.from_env()
