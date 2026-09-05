import pytest

from ai_daily_brief.digest import build_report
from ai_daily_brief.email_sender import send_report


def test_send_report_requires_smtp_configuration(monkeypatch):
    monkeypatch.delenv("AI_BRIEF_SMTP_HOST", raising=False)
    with pytest.raises(RuntimeError, match="SMTP_HOST"):
        send_report(build_report([], []), "test@example.com")
