"""Content normalization, deduplication, and event clustering."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime
from difflib import SequenceMatcher
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .sources import RawItem

_TRACKING_PARAMS = {"fbclid", "gclid", "ref", "ref_", "utm_campaign", "utm_medium", "utm_source"}
_WORD_RE = re.compile(r"[\w]+", re.UNICODE)


def normalize_url(url: str) -> str:
    """Remove tracking parameters and normalize URL formatting."""
    parts = urlsplit(url.strip())
    query = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if key.lower() not in _TRACKING_PARAMS and not key.lower().startswith("utm_")
    ]
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, urlencode(query), ""))


def content_hash(item: RawItem) -> str:
    """Create a stable hash from normalized title and excerpt."""
    value = " ".join((item.title, item.content_excerpt)).lower()
    value = " ".join(value.split())
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _title_tokens(title: str) -> set[str]:
    return set(_WORD_RE.findall(title.lower()))


def title_similarity(left: str, right: str) -> float:
    """Combine token overlap and character similarity for duplicate detection."""
    left_tokens, right_tokens = _title_tokens(left), _title_tokens(right)
    if not left_tokens or not right_tokens:
        return 0.0
    jaccard = len(left_tokens & right_tokens) / len(left_tokens | right_tokens)
    sequence = SequenceMatcher(None, left.lower(), right.lower()).ratio()
    return max(jaccard, sequence)


def deduplicate_items(items: list[RawItem], similarity_threshold: float = 0.82) -> list[RawItem]:
    """Keep the first item for duplicate URLs, hashes, or highly similar titles."""
    unique: list[RawItem] = []
    seen_urls: set[str] = set()
    seen_hashes: set[str] = set()
    for item in items:
        url = normalize_url(item.url)
        item_hash = content_hash(item)
        if url in seen_urls or item_hash in seen_hashes:
            continue
        if any(title_similarity(item.title, existing.title) >= similarity_threshold for existing in unique):
            continue
        unique.append(item)
        seen_urls.add(url)
        seen_hashes.add(item_hash)
    return unique


@dataclass(frozen=True)
class EventCluster:
    canonical: RawItem
    related: tuple[RawItem, ...]

    @property
    def source_count(self) -> int:
        return len({item.source_id for item in self.related})


def _within_window(left: datetime | None, right: datetime | None, hours: int) -> bool:
    if left is None or right is None:
        return True
    return abs((left - right).total_seconds()) <= hours * 3600


def cluster_events(items: list[RawItem], similarity_threshold: float = 0.68) -> list[EventCluster]:
    """Group likely reports of the same event while retaining every source item."""
    clusters: list[list[RawItem]] = []
    for item in items:
        matching = next(
            (
                cluster
                for cluster in clusters
                if _within_window(item.published_at, cluster[0].published_at, 48)
                and any(
                    title_similarity(item.title, member.title) >= similarity_threshold
                    for member in cluster
                )
            ),
            None,
        )
        if matching is None:
            clusters.append([item])
        else:
            matching.append(item)
    return [EventCluster(canonical=cluster[0], related=tuple(cluster)) for cluster in clusters]
