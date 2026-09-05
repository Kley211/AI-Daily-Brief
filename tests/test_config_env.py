from ai_daily_brief.config import load_dotenv


def test_load_dotenv_reads_values_without_overwriting(monkeypatch, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("AI_BRIEF_TEST_VALUE=loaded\n# ignored\n", encoding="utf-8")
    monkeypatch.delenv("AI_BRIEF_TEST_VALUE", raising=False)

    load_dotenv(str(env_file))

    assert __import__("os").environ["AI_BRIEF_TEST_VALUE"] == "loaded"
