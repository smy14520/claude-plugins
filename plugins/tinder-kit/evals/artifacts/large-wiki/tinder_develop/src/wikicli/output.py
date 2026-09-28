"""Human-readable and JSON rendering for every command."""
from __future__ import annotations

from .model import AMBIGUOUS, DEAD, OK, DoctorReport, Page, ResolvedLink, TagEntry, WikiLink
from .search import SearchResult


def _label(page: Page) -> str:
    return page.path.as_posix()


# -- links / backlinks ----------------------------------------------


def format_links(page: Page, links: list[ResolvedLink]) -> str:
    if not links:
        return f"{_label(page)} has no outgoing wiki links."
    lines = [f"{_label(page)} — {len(links)} outgoing wiki link(s):"]
    for item in links:
        raw = f"[[{item.link.raw}]]"
        if item.status == OK:
            lines.append(f"  L{item.link.line}  {raw} -> {_label(item.resolved)}")
        elif item.status == DEAD:
            lines.append(f"  L{item.link.line}  {raw} -> (dead)")
        else:
            names = ", ".join(_label(c) for c in item.candidates)
            lines.append(f"  L{item.link.line}  {raw} -> (ambiguous: {names})")
    return "\n".join(lines)


def links_payload(page: Page, links: list[ResolvedLink]) -> dict:
    return {
        "page": _label(page),
        "links": [
            {
                "raw": item.link.raw,
                "display": item.link.display,
                "line": item.link.line,
                "status": item.status,
                "resolved": _label(item.resolved) if item.resolved else None,
                "candidates": [_label(c) for c in item.candidates],
            }
            for item in links
        ],
    }


def format_backlinks(page: Page, backlinks: list[WikiLink]) -> str:
    if not backlinks:
        return f"No pages link to {_label(page)}."
    lines = [f"{_label(page)} — {len(backlinks)} backlink(s):"]
    for link in backlinks:
        lines.append(f"  {_label(link.page)}:L{link.line}  [[{link.raw}]]")
    return "\n".join(lines)


def backlinks_payload(page: Page, backlinks: list[WikiLink]) -> dict:
    return {
        "page": _label(page),
        "backlinks": [
            {"source": _label(link.page), "line": link.line, "raw": link.raw}
            for link in backlinks
        ],
    }


# -- tags -------------------------------------------------------------


def format_tags(entries: list[TagEntry]) -> str:
    if not entries:
        return "No tags found in this vault."
    lines = [f"{len(entries)} tag(s), nested tags indented under their parent:"]
    for entry in entries:
        indent = "  " * entry.tag.count("/")
        lines.append(f"{indent}#{entry.tag} ({len(entry.pages)})")
    return "\n".join(lines)


def tags_payload(entries: list[TagEntry]) -> dict:
    return {
        "tags": [{"tag": e.tag, "count": len(e.pages)} for e in entries],
    }


def format_tag_pages(tag: str, entries: list[TagEntry]) -> str:
    if not entries:
        return f"No pages carry #{tag} (or its children)."
    lines = [f"#{tag} — pages carrying it or any child tag:"]
    for entry in entries:
        where = f":L{entry.first_line}" if entry.first_line else ""
        for page in entry.pages:
            lines.append(f"  {_label(page)}{where}  #{entry.tag}")
    return "\n".join(lines)


def tag_pages_payload(tag: str, entries: list[TagEntry]) -> dict:
    return {
        "tag": tag,
        "matches": [
            {"tag": e.tag, "pages": [_label(p) for p in e.pages]} for e in entries
        ],
    }


# -- search -----------------------------------------------------------


def format_search(query: list[str], results: list[SearchResult]) -> str:
    if not results:
        return f"No pages match: {' '.join(query)}"
    lines = [f"{len(results)} result(s) for: {' '.join(query)}"]
    for rank, result in enumerate(results, 1):
        lines.append(
            f"{rank}. {_label(result.page)}"
            f"  (title hits: {result.title_hits}, content hits: {result.content_hits})"
        )
        for hit in result.hits:
            lines.append(f"   L{hit.line}: {hit.snippet}")
    return "\n".join(lines)


def search_payload(query: list[str], results: list[SearchResult]) -> dict:
    return {
        "query": query,
        "results": [
            {
                "page": _label(r.page),
                "title_hits": r.title_hits,
                "content_hits": r.content_hits,
                "hits": [{"line": h.line, "snippet": h.snippet} for h in r.hits],
            }
            for r in results
        ],
    }


# -- doctor -----------------------------------------------------------


def format_doctor(report: DoctorReport) -> str:
    lines: list[str] = []
    if report.dead:
        lines.append(f"Dead links ({len(report.dead)}):")
        lines += [
            f"  {_label(r.link.page)}:L{r.link.line}  [[{r.link.raw}]]" for r in report.dead
        ]
    if report.ambiguous:
        lines.append(f"Ambiguous links ({len(report.ambiguous)}):")
        for r in report.ambiguous:
            names = ", ".join(_label(c) for c in r.candidates)
            lines.append(f"  {_label(r.link.page)}:L{r.link.line}  [[{r.link.raw}]] -> {names}")
    if report.orphans:
        lines.append(f"Orphan pages ({len(report.orphans)}):")
        lines += [f"  {_label(p)}" for p in report.orphans]
    if not lines:
        return "No dead links, no ambiguous links, no orphan pages. Vault is healthy."
    lines.append("")
    lines.append(
        f"{len(report.dead)} dead, {len(report.ambiguous)} ambiguous, {len(report.orphans)} orphan(s)."
    )
    return "\n".join(lines)


def doctor_payload(report: DoctorReport) -> dict:
    return {
        "dead_links": [
            {"page": _label(r.link.page), "line": r.link.line, "raw": r.link.raw}
            for r in report.dead
        ],
        "ambiguous_links": [
            {
                "page": _label(r.link.page),
                "line": r.link.line,
                "raw": r.link.raw,
                "candidates": [_label(c) for c in r.candidates],
            }
            for r in report.ambiguous
        ],
        "orphan_pages": [_label(p) for p in report.orphans],
    }
