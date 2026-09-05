"""Small dependency-free RSS and Atom parser."""

from __future__ import annotations

import html
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Callable

from .base import RawItem
from ..tls import default_context

_TAG_RE = re.compile(r"<[^>]+>")


def fetch_xml(url: str, timeout: int = 20) -> bytes:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "ai-daily-brief/0.1 (+public-feed-reader)"},
    )
    with urllib.request.urlopen(request, timeout=timeout, context=default_context()) as response:
        return response.read()


def _text(element: ET.Element | None) -> str:
    if element is None:
        return ""
    return " ".join("".join(element.itertext()).split())


def _strip_markup(value: str) -> str:
    cleaned = html.unescape(_TAG_RE.sub(" ", value))
    cleaned = re.sub(r"\s+([,.;:!?])", r"\1", cleaned)
    return " ".join(cleaned.split())


def _parse_datetime(value: str) -> datetime | None:
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _child(element: ET.Element, *names: str) -> ET.Element | None:
    wanted = set(names)
    return next((child for child in element if _local_name(child.tag) in wanted), None)


def _link(element: ET.Element) -> str:
    for child in element:
        if _local_name(child.tag) != "link":
            continue
        href = child.attrib.get("href")
        if href and child.attrib.get("rel", "alternate") == "alternate":
            return href
        if child.text and child.text.strip():
            return child.text.strip()
    return ""


def parse_feed(payload: bytes, source_id: str) -> list[RawItem]:
    root = ET.fromstring(payload)
    channel = _child(root, "channel")
    entries = list(channel) if channel is not None else list(root)
    items: list[RawItem] = []
    for entry in entries:
        kind = _local_name(entry.tag)
        if kind not in {"item", "entry"}:
            continue
        title = _text(_child(entry, "title"))
        url = _link(entry)
        external_id = _text(_child(entry, "guid", "id")) or url or title
        summary = _text(_child(entry, "description", "summary", "content"))
        published = _text(_child(entry, "pubDate", "published", "updated"))
        author = _text(_child(entry, "author", "creator"))
        if not title or not url:
            continue
        items.append(
            RawItem(
                source_id=source_id,
                external_id=external_id,
                title=title,
                url=url,
                published_at=_parse_datetime(published),
                content_excerpt=_strip_markup(summary),
                author=author,
            )
        )
    return items


def load_feed(
    url: str,
    source_id: str,
    loader: Callable[[str], bytes] = fetch_xml,
) -> list[RawItem]:
    return parse_feed(loader(url), source_id)
