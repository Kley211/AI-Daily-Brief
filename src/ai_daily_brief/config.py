"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def load_dotenv(path: str = ".env") -> None:
    """Load simple KEY=VALUE pairs without requiring an extra dependency."""
    env_path = Path(path)
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip().strip("\"'")
        os.environ.setdefault(key, value)


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if parsed <= 0:
        raise ValueError(f"{name} must be greater than zero")
    return parsed


def _env_str(name: str, default: str) -> str:
    value = os.getenv(name)
    return default if value is None or value == "" else value


@dataclass(frozen=True)
class Settings:
    timezone: str = "Asia/Shanghai"
    send_time: str = "08:00"
    lookback_hours: int = 24
    max_digest_items: int = 10
    recipient: str = ""

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        return cls(
            timezone=_env_str("AI_BRIEF_TIMEZONE", cls.timezone),
            send_time=_env_str("AI_BRIEF_SEND_TIME", cls.send_time),
            lookback_hours=_env_int("AI_BRIEF_LOOKBACK_HOURS", cls.lookback_hours),
            max_digest_items=_env_int(
                "AI_BRIEF_MAX_DIGEST_ITEMS", cls.max_digest_items
            ),
            recipient=_env_str("AI_BRIEF_RECIPIENT", ""),
        )
