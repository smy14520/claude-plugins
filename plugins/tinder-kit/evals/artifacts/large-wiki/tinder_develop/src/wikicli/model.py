"""Core domain model: Page, WikiLink, TagHit and resolution results.

Terms follow ``.forge/CONTEXT.md``: a Page is identified by its filename
stem, a WikiLink is a ``[[target]]`` reference, and every link resolves to
exactly one of ok / dead / ambiguous.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

OK = "ok"
DEAD = "dead"
AMBIGUOUS = "ambiguous"


@dataclass(frozen=True)
class Page:
    """A markdown file in the vault, identified by its filename stem."""

    path: Path  # relative to the vault root, e.g. ``notes/foo.md``
    title: str | None = None  # first H1 heading outside code fences

    @property
    def name(self) -> str:
        """The page's identity: filename without the ``.md`` suffix."""
        return self.path.name.removesuffix(".md")


@dataclass(frozen=True)
class WikiLink:
    """A ``[[target]]`` reference found on a specific line of a page."""

    page: Page
    line: int  # 1-based, absolute within the file
    raw: str  # target text as written (before any ``|``), stripped
    display: str | None = None  # alias text after ``|``, if present

    @property
    def target(self) -> str:
        """The resolution target: anchor section dropped, then an optional
        ``.md`` suffix removed. Anchors are out of scope (``[[Foo#Bar]]``
        still refers to page ``Foo``)."""
        base = self.raw.split("#", 1)[0].strip()
        if base[-3:].lower() == ".md":
            base = base[:-3]
        return base


@dataclass(frozen=True)
class ResolvedLink:
    """A WikiLink plus the outcome of resolving it against the vault."""

    link: WikiLink
    status: str  # one of OK / DEAD / AMBIGUOUS
    resolved: Page | None = None
    candidates: tuple[Page, ...] = ()


@dataclass(frozen=True)
class ParsedPage:
    """A Page plus everything parsed out of it — the unit the index caches."""

    page: Page
    title: str | None
    body: str
    body_start: int  # 1-based line number of the first body line
    fingerprint: str  # size:mtime_ns of the source file at parse time
    links: tuple[WikiLink, ...]
    tags: tuple["TagHit", ...]


@dataclass(frozen=True)
class TagHit:
    """A single tag occurrence on a page."""

    page: Page
    tag: str
    line: int | None  # None when the tag comes from frontmatter


@dataclass
class TagEntry:
    """A tag aggregated across the vault (one entry per casefolded tag)."""

    tag: str  # display casing (first occurrence wins)
    key: str  # casefolded grouping key
    pages: list[Page] = field(default_factory=list)
    first_line: int | None = None


@dataclass(frozen=True)
class DoctorReport:
    """Everything the doctor command found wrong with a vault."""

    dead: tuple[ResolvedLink, ...]
    ambiguous: tuple[ResolvedLink, ...]
    orphans: tuple[Page, ...]  # pages with no Backlink at all

    @property
    def has_findings(self) -> bool:
        return bool(self.dead or self.ambiguous or self.orphans)
