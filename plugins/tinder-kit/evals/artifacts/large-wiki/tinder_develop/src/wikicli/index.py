"""Vault scanning plus the single-file index cache (``.wiki_index.json``).

The ``.md`` files are the only carrier of truth; the index file is a pure
cache. Every invocation stats the whole vault, reuses per-page records whose
fingerprint (``size:mtime_ns``) is unchanged, re-parses changed pages, drops
vanished ones, and atomically rewrites the file only when something changed.
A missing, corrupt, or foreign-version index is silently rebuilt. No
database, ever — this module is the persistence adapter of the LinkGraph
subsystem (see ``linkgraph.py``).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from .linkgraph import Vault
from .model import Page, ParsedPage, TagHit, WikiLink
from .parser import (
    extract_frontmatter_tags,
    extract_links,
    extract_tags,
    extract_title,
    mask_code,
    split_frontmatter,
)

INDEX_FILENAME = ".wiki_index.json"
INDEX_VERSION = 1


def load_vault(root: Path) -> Vault:
    """Scan *root*, refresh the index cache, and return the built Vault."""
    entries = _scan(root)
    cached = _load(root).get("pages", {})
    parsed: dict[Page, ParsedPage] = {}
    dirty = False
    for rel, path in entries.items():
        fingerprint = _fingerprint(path)
        record = cached.get(rel)
        if record is not None and record.get("fingerprint") == fingerprint:
            reused = _from_record(rel, record)
            parsed[reused.page] = reused
        else:
            fresh = _parse(path, rel, fingerprint)
            parsed[fresh.page] = fresh
            dirty = True
    if set(cached) - set(entries):
        dirty = True  # pages vanished since the last run
    vault = Vault(root=root, parsed=parsed)
    if dirty:
        _save(root, parsed)
    return vault


def _scan(root: Path) -> dict[str, Path]:
    """Every visible ``*.md`` under *root*, as {posix relpath: path}."""
    found: dict[str, Path] = {}
    for path in sorted(root.rglob("*.md")):
        rel = path.relative_to(root)
        if any(part.startswith(".") for part in rel.parts):
            continue
        found[rel.as_posix()] = path
    return found


def _fingerprint(path: Path) -> str:
    stat = path.stat()
    return f"{stat.st_size}:{stat.st_mtime_ns}"


def _parse(path: Path, rel: str, fingerprint: str) -> ParsedPage:
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    frontmatter, body, body_start = split_frontmatter(text)
    masked = mask_code(body.splitlines(), body_start)
    page = Page(path=Path(rel), title=extract_title(masked))
    links = tuple(extract_links(page, masked))
    tags = tuple(
        TagHit(page=page, tag=tag, line=line) for line, tag in extract_tags(masked)
    ) + tuple(
        TagHit(page=page, tag=tag, line=None)
        for tag in extract_frontmatter_tags(frontmatter)
    )
    return ParsedPage(
        page=page,
        title=page.title,
        body=body,
        body_start=body_start,
        fingerprint=fingerprint,
        links=links,
        tags=tags,
    )


def _from_record(rel: str, record: dict) -> ParsedPage:
    page = Page(path=Path(rel), title=record.get("title"))
    links = tuple(
        WikiLink(page=page, line=item["line"], raw=item["raw"], display=item.get("display"))
        for item in record.get("links", [])
    )
    tags = tuple(
        TagHit(page=page, tag=item["tag"], line=item.get("line"))
        for item in record.get("tags", [])
    )
    return ParsedPage(
        page=page,
        title=record.get("title"),
        body=record.get("body", ""),
        body_start=record.get("body_start", 1),
        fingerprint=record["fingerprint"],
        links=links,
        tags=tags,
    )


def _to_record(parsed: ParsedPage) -> dict:
    return {
        "fingerprint": parsed.fingerprint,
        "title": parsed.title,
        "body": parsed.body,
        "body_start": parsed.body_start,
        "links": [
            {"raw": link.raw, "line": link.line, "display": link.display}
            for link in parsed.links
        ],
        "tags": [{"tag": tag.tag, "line": tag.line} for tag in parsed.tags],
    }


def _load(root: Path) -> dict:
    try:
        data = json.loads((root / INDEX_FILENAME).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict) or data.get("version") != INDEX_VERSION:
        return {}
    if not isinstance(data.get("pages"), dict):
        return {}
    return data


def _save(root: Path, parsed: dict[Page, ParsedPage]) -> None:
    payload = {
        "version": INDEX_VERSION,
        "pages": {
            page.path.as_posix(): _to_record(p)
            for page, p in sorted(parsed.items(), key=lambda item: item[0].path.as_posix())
        },
    }
    index_path = root / INDEX_FILENAME
    tmp = root / (INDEX_FILENAME + ".tmp")
    try:
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
        tmp.replace(index_path)
    except OSError as exc:
        print(
            f"wiki-cli: could not write {INDEX_FILENAME}, "
            f"continuing with the in-memory index ({exc})",
            file=sys.stderr,
        )
