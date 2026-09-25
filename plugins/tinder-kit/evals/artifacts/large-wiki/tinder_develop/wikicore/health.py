"""体检：死链与孤岛页面诊断。

- DeadLink：指向不存在 PageName 的 WikiLink；
- Orphan：无任何入链的页面（CONTEXT.md），`entries` 中的入口页豁免。
"""

from __future__ import annotations

from dataclasses import dataclass

from .model import Index


@dataclass(frozen=True)
class DeadLink:
    page: str
    line: int
    target: str


@dataclass(frozen=True)
class HealthReport:
    dead_links: list[DeadLink]
    orphans: list[str]


def check(index: Index, entries=()) -> HealthReport:
    exempt = {entry.strip().casefold() for entry in entries}

    dead_links = [
        DeadLink(name, link.line, link.target)
        for name, info in index.pages.items()
        for link in info.links
        if index.resolve(link.target) is None
    ]
    dead_links.sort(key=lambda d: (d.page, d.line, d.target))

    orphans = sorted(
        name
        for name in index.pages
        if not index.backlinks(name) and name.casefold() not in exempt
    )
    return HealthReport(dead_links=dead_links, orphans=orphans)
