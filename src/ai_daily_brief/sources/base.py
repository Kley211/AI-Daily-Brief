"""Shared contracts for source adapters."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class RawItem:
    source_id: str
    external_id: str
    title: str
    url: str
    published_at: datetime | None
    content_excerpt: str = ""
    author: str = ""
    metadata: dict[str, str] = field(default_factory=dict)


class SourceAdapter(Protocol):
    source_id: str

    def fetch(self) -> list[RawItem]:
        """Fetch and parse new items from a public source."""
