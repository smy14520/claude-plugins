"""LinkGraph subsystem: page registries, WikiLink resolution, outgoing links,
Backlinks, tag aggregation, and the doctor diagnosis — pure in-memory views
over per-page parsed records (``index.py`` is its persistence adapter).

Name matching is Unicode casefolded throughout so Chinese filenames and case
differences are handled robustly.
"""
from __future__ import annotations

from pathlib import Path

from .model import (
    AMBIGUOUS,
    DEAD,
    OK,
    DoctorReport,
    Page,
    ParsedPage,
    ResolvedLink,
    TagEntry,
    TagHit,
    WikiLink,
)
from .search import SearchResult, search_pages


class Vault:
    """An indexed, read-only view of a vault directory."""

    def __init__(self, root: Path, parsed: dict[Page, ParsedPage]):
        self.root = root
        self.pages = list(parsed)
        self._parsed = parsed
        self._by_stem: dict[str, list[Page]] = {}
        self._by_path: dict[str, Page] = {}
        for page in self.pages:
            self._by_stem.setdefault(page.name.casefold(), []).append(page)
            self._by_path[page.path.with_suffix("").as_posix().casefold()] = page
        self._backlinks: dict[Page, list[WikiLink]] | None = None

    # -- resolution ---------------------------------------------------

    def resolve(self, target: str) -> tuple[str, Page | None, tuple[Page, ...]]:
        """Resolve a link target to ``(status, page, candidates)``.

        Sub-path targets (``notes/foo``) match by relative path first, then
        fall back to the stem; bare stems match globally and are ambiguous
        when several pages share the name. Matching is casefolded.
        """
        name = target.strip()
        if name[-3:].lower() == ".md":
            name = name[:-3]
        hit = self._by_path.get(name.casefold())
        if hit is not None:
            return OK, hit, ()
        stem = name.rsplit("/", 1)[-1].casefold()
        candidates = tuple(self._by_stem.get(stem, ()))
        if len(candidates) == 1:
            return OK, candidates[0], ()
        if len(candidates) > 1:
            return AMBIGUOUS, None, candidates
        return DEAD, None, ()

    # -- links --------------------------------------------------------

    def links_of(self, page: Page) -> list[WikiLink]:
        return list(self._parsed[page].links)

    def resolved_links_of(self, page: Page) -> list[ResolvedLink]:
        resolved = []
        for link in self.links_of(page):
            status, target, candidates = self.resolve(link.target)
            resolved.append(
                ResolvedLink(link=link, status=status, resolved=target, candidates=candidates)
            )
        return resolved

    def backlinks_of(self, page: Page) -> list[WikiLink]:
        """All WikiLinks (from any page, including itself) that resolve here."""
        if self._backlinks is None:
            incoming: dict[Page, list[WikiLink]] = {}
            for source in self.pages:
                for link in self.links_of(source):
                    status, target, _ = self.resolve(link.target)
                    if status == OK and target is not None:
                        incoming.setdefault(target, []).append(link)
            self._backlinks = incoming
        return list(self._backlinks.get(page, ()))

    # -- tags ---------------------------------------------------------

    def tags_of(self, page: Page) -> list[TagHit]:
        return list(self._parsed[page].tags)

    def tag_index(self) -> list[TagEntry]:
        """Aggregate tags across the vault: one entry per casefolded tag.

        A tag counts once per page; the display casing is the first
        occurrence in page/line order. Entries are sorted by key, so nested
        tags (``a/b``) land right under their parent (``a``).
        """
        entries: dict[str, TagEntry] = {}
        for page in self.pages:
            seen: set[str] = set()
            for hit in self._parsed[page].tags:
                key = hit.tag.casefold()
                if key in seen:  # a tag counts once per page
                    continue
                seen.add(key)
                entry = entries.get(key)
                if entry is None:
                    entry = TagEntry(tag=hit.tag, key=key, first_line=hit.line)
                    entries[key] = entry
                entry.pages.append(page)
        return sorted(entries.values(), key=lambda e: e.key)

    # -- search -------------------------------------------------------

    def search(self, keywords: list[str]) -> list[SearchResult]:
        entries = [
            (page, parsed.title or "", parsed.body, parsed.body_start)
            for page, parsed in self._parsed.items()
        ]
        return search_pages(entries, keywords)

    # -- doctor -------------------------------------------------------

    def doctor(self) -> DoctorReport:
        """Collect Dead Links, Ambiguous Links and Orphan Pages.

        Only links that resolve (status OK) grant Backlink membership; an
        ambiguous link points at "some page named X", so it satisfies none.
        """
        dead: list[ResolvedLink] = []
        ambiguous: list[ResolvedLink] = []
        linked: set[Page] = set()
        for page in self.pages:
            for resolved in self.resolved_links_of(page):
                if resolved.status == DEAD:
                    dead.append(resolved)
                elif resolved.status == AMBIGUOUS:
                    ambiguous.append(resolved)
                elif resolved.resolved is not None:
                    linked.add(resolved.resolved)
        orphans = tuple(page for page in self.pages if page not in linked)
        return DoctorReport(dead=tuple(dead), ambiguous=tuple(ambiguous), orphans=orphans)
