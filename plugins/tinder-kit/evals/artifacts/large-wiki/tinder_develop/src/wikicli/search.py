"""Keyword full-text search over page titles and bodies.

Matching is Unicode-casefolded substring containment (no tokenisation), so it
works naturally on Chinese text. All keywords must match (AND); ranking puts
title hits first, then denser content hits. Bodies are searched as raw text —
code blocks included — matching grep-like expectations.
"""
from __future__ import annotations

from dataclasses import dataclass

from .model import Page

MAX_HITS_PER_PAGE = 3


@dataclass(frozen=True)
class SearchHit:
    line: int  # 1-based, absolute within the file
    snippet: str


@dataclass(frozen=True)
class SearchResult:
    page: Page
    title_hits: int  # number of keywords present in the title
    content_hits: int  # total keyword occurrences across the body
    hits: tuple[SearchHit, ...]


def search_pages(
    entries: "list[tuple[Page, str, str, int]]",
    keywords: list[str],
    max_hits: int = MAX_HITS_PER_PAGE,
) -> list[SearchResult]:
    """Search ``(page, title, body, body_start_line)`` entries.

    Every keyword must appear in the title or the body (AND over
    title-or-content per keyword).
    """
    folded_keywords = [k.casefold() for k in keywords if k]
    if not folded_keywords:
        return []
    results: list[SearchResult] = []
    for page, title, body, body_start in entries:
        folded_title = title.casefold()
        folded_body = body.casefold()
        if any(k not in folded_title and k not in folded_body for k in folded_keywords):
            continue
        title_hits = sum(1 for k in folded_keywords if k in folded_title)
        content_hits = sum(folded_body.count(k) for k in folded_keywords)
        hits: list[SearchHit] = []
        for offset, line in enumerate(body.splitlines()):
            folded_line = line.casefold()
            if any(k in folded_line for k in folded_keywords):
                hits.append(SearchHit(line=body_start + offset, snippet=line.strip()))
                if len(hits) >= max_hits:
                    break
        results.append(
            SearchResult(page=page, title_hits=title_hits, content_hits=content_hits, hits=tuple(hits))
        )
    results.sort(key=lambda r: (-r.title_hits, -r.content_hits, r.page.path.as_posix()))
    return results
