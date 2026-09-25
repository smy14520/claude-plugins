"""全文检索：大小写不敏感子串、多词 AND、按命中次数粗排（Q6）。"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .model import Page, WikiIndex


@dataclass
class SearchHit:
    page: Page
    count: int
    snippet: str


def search(index: WikiIndex, terms: list[str]) -> list[SearchHit]:
    """内存线性扫描（子串语义下的最优形态）；全部关键词命中才算命中。"""
    lowered = [t.casefold() for t in terms if t]
    if not lowered:
        return []
    hits: list[SearchHit] = []
    for page in index.pages:
        haystack = page.body.casefold()
        counts = [haystack.count(term) for term in lowered]
        if all(counts):
            hits.append(SearchHit(page, sum(counts), _snippet(page.body, lowered[0])))
    hits.sort(key=lambda h: (-h.count, h.page.title, h.page.path))
    return hits


def _snippet(body: str, term: str, window: int = 40) -> str:
    """首个命中所在行；过长时以命中点为中心截窗。"""
    match = re.search(re.escape(term), body, re.IGNORECASE)
    if not match:
        return ""
    position = match.start()
    line_start = body.rfind("\n", 0, position) + 1
    line_end = body.find("\n", position)
    if line_end == -1:
        line_end = len(body)
    line = body[line_start:line_end].strip()
    if len(line) <= window * 2:
        return line
    rel = position - line_start
    start = max(0, rel - window)
    end = min(len(line), rel + window)
    prefix = "…" if start > 0 else ""
    suffix = "…" if end < len(line) else ""
    return f"{prefix}{line[start:end].strip()}{suffix}"
