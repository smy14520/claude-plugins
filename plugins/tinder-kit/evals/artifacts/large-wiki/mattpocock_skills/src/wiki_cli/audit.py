"""体检：对 Vault 的只读诊断。

缺陷类别恰为四种（CONTEXT.md「体检」条目）：
死链、孤岛页（零入链）、重名页、畸形 Frontmatter。
空页面、无标签页、未验证的锚点都不是缺陷。
"""

from __future__ import annotations

from dataclasses import dataclass

from .model import Index, Page
from .query import LinkStatus, resolve_target


@dataclass(frozen=True)
class DeadLink:
    page: str
    path: str
    line: int
    raw: str


@dataclass(frozen=True)
class DuplicateName:
    name: str
    paths: tuple[str, ...]


@dataclass(frozen=True)
class AuditReport:
    dead_links: tuple[DeadLink, ...] = ()
    orphans: tuple[Page, ...] = ()
    duplicates: tuple[DuplicateName, ...] = ()
    malformed_frontmatter: tuple[Page, ...] = ()

    @property
    def defect_count(self) -> int:
        return (
            len(self.dead_links)
            + len(self.orphans)
            + len(self.duplicates)
            + len(self.malformed_frontmatter)
        )

    @property
    def has_defects(self) -> bool:
        return self.defect_count > 0

    def as_json(self) -> dict:
        return {
            "dead_links": [
                {
                    "page": d.page,
                    "path": d.path,
                    "line": d.line,
                    "target": d.raw,
                }
                for d in self.dead_links
            ],
            "orphans": [
                {"name": p.name, "path": p.rel_path} for p in self.orphans
            ],
            "duplicates": [
                {"name": d.name, "paths": list(d.paths)} for d in self.duplicates
            ],
            "malformed_frontmatter": [
                {"name": p.name, "path": p.rel_path}
                for p in self.malformed_frontmatter
            ],
        }


def audit(index: Index) -> AuditReport:
    by_name = index.by_name()
    dead: list[DeadLink] = []
    linked_names: set[str] = set()

    for page in index.pages:
        for link in page.links:
            if link.external:
                continue
            status, _ = resolve_target(index, link.target)
            if status == LinkStatus.RESOLVED:
                linked_names.add(link.target)
            elif status == LinkStatus.DEAD:
                dead.append(
                    DeadLink(
                        page=page.name,
                        path=page.rel_path,
                        line=link.line,
                        raw=link.raw,
                    )
                )
            # 歧义目标不算死链，重名缺陷已覆盖其根因

    dead.sort(key=lambda d: (d.path, d.line))
    orphans = tuple(p for p in index.pages if p.name not in linked_names)
    duplicates = tuple(
        DuplicateName(name=name, paths=tuple(sorted(p.rel_path for p in pages)))
        for name, pages in sorted(by_name.items())
        if len(pages) > 1
    )
    malformed = tuple(p for p in index.pages if p.malformed_frontmatter)

    return AuditReport(
        dead_links=tuple(dead),
        orphans=orphans,
        duplicates=duplicates,
        malformed_frontmatter=malformed,
    )
