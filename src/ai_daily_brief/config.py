"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass


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


@dataclass(frozen=True)
class Settings:
    timezone: str = "Asia/Shanghai"
    send_time: str = "08:00"
    lookback_hours: int = 24
    max_digest_items: int = 10
    recipient: str = ""

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            timezone=os.getenv("AI_BRIEF_TIMEZONE", cls.timezone),
            send_time=os.getenv("AI_BRIEF_SEND_TIME", cls.send_time),
            lookback_hours=_env_int("AI_BRIEF_LOOKBACK_HOURS", cls.lookback_hours),
            max_digest_items=_env_int(
                "AI_BRIEF_MAX_DIGEST_ITEMS", cls.max_digest_items
            ),
            recipient=os.getenv("AI_BRIEF_RECIPIENT", ""),
        )
