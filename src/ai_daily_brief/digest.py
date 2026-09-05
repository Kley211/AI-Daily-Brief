"""Daily digest assembly and email rendering."""

from __future__ import annotations

import html
from dataclasses import dataclass
from datetime import date

from .enrichment import EnrichedEvent
from .processing import EventCluster


@dataclass(frozen=True)
class DigestEntry:
    event: EventCluster
    enrichment: EnrichedEvent


@dataclass(frozen=True)
class DigestReport:
    digest_date: date
    conclusion: str
    entries: tuple[DigestEntry, ...]


def build_report(events: list[EventCluster], enrichments: list[EnrichedEvent], max_items: int = 10, digest_date: date | None = None) -> DigestReport:
    entries = [DigestEntry(event, enrichment) for event, enrichment in zip(events, enrichments)]
    rank = {"high": 0, "medium": 1, "low": 2}
    entries.sort(key=lambda entry: (rank.get(entry.enrichment.importance, 9), entry.event.canonical.title.lower()))
    entries = entries[:max_items]
    conclusion = "今天没有发现需要重点关注的 AI 更新。" if not entries else f"今天筛选出 {len(entries)} 条值得关注的 AI 情报，优先关注高重要性事件。"
    return DigestReport(digest_date or date.today(), conclusion, tuple(entries))


def render_text(report: DigestReport) -> str:
    lines = [f"AI Daily Brief | {report.digest_date.isoformat()}", "", "今日结论", report.conclusion, ""]
    if not report.entries:
        lines.append("暂无重点消息。")
    for index, entry in enumerate(report.entries, 1):
        item, value = entry.event.canonical, entry.enrichment
        lines.extend([f"{index}. {item.title}", f"摘要：{value.summary}", f"为什么重要：{value.why_it_matters}", f"分类：{value.category} | 重要性：{value.importance} | 状态：{value.confidence}", f"来源：{item.source_id} | {item.url}", ""])
    return "\n".join(lines).strip() + "\n"


def render_html(report: DigestReport) -> str:
    sections = ["<!doctype html><html><head><meta charset='utf-8'><title>AI Daily Brief</title>", "<style>body{font-family:Arial,sans-serif;max-width:760px;margin:24px auto;padding:0 16px;color:#222}article{border-top:1px solid #ddd;padding:16px 0}small{color:#666}a{color:#1558b0}</style></head><body>", f"<h1>AI Daily Brief | {report.digest_date.isoformat()}</h1>", f"<h2>今日结论</h2><p>{html.escape(report.conclusion)}</p>"]
    if not report.entries:
        sections.append("<p>暂无重点消息。</p>")
    for index, entry in enumerate(report.entries, 1):
        item, value = entry.event.canonical, entry.enrichment
        sections.append("<article>" f"<h2>{index}. {html.escape(item.title)}</h2>" f"<p>{html.escape(value.summary)}</p>" f"<p><strong>为什么重要：</strong>{html.escape(value.why_it_matters)}</p>" f"<small>分类：{html.escape(value.category)} | 重要性：{html.escape(value.importance)} | 状态：{html.escape(value.confidence)} | 来源：{html.escape(item.source_id)}</small> " f"<a href='{html.escape(item.url, quote=True)}'>查看原文</a>" "</article>")
    sections.append("</body></html>")
    return "".join(sections)
