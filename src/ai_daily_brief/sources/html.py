"""Minimal public listing-page parser for sources without RSS."""

from __future__ import annotations

import html
import os
import re
import ssl
import urllib.request
from html.parser import HTMLParser
from urllib.parse import urljoin

from ..tls import default_context
from .base import RawItem


def fetch_text(url: str, timeout: int = 20) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "ai-daily-brief/0.1"})
    with urllib.request.urlopen(request, timeout=timeout, context=default_context()) as response:
        return response.read().decode(response.headers.get_content_charset() or "utf-8", errors="replace")


class _LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.current_href = ""
        self.current_text: list[str] = []
        self.links: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            self.current_href = dict(attrs).get("href") or ""
            self.current_text = []

    def handle_data(self, data: str) -> None:
        if self.current_href:
            self.current_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self.current_href:
            title = " ".join("".join(self.current_text).split())
            self.links.append((self.current_href, title))
            self.current_href = ""
            self.current_text = []


def parse_listing(payload: str, source_id: str, base_url: str, path_pattern: str) -> list[RawItem]:
    parser = _LinkParser()
    parser.feed(payload)
    seen: set[str] = set()
    items: list[RawItem] = []
    for href, title in parser.links:
        url = urljoin(base_url, html.unescape(href))
        if not title or url in seen or not re.search(path_pattern, url):
            continue
        seen.add(url)
        items.append(RawItem(source_id, url, title, url, None))
    return items[:100]


def load_listing(url: str, source_id: str, path_pattern: str) -> list[RawItem]:
    return parse_listing(fetch_text(url), source_id, url, path_pattern)
