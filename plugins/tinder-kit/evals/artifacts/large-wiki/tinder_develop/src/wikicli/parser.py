"""Markdown parsing primitives (the agreed parsing seam).

Fenced code blocks and inline code are blanked out before any matching, so
``[[link]]`` and ``#tag`` syntax inside code never counts (backtick runs of
any length delimit inline spans). Frontmatter is handled by a line-level
parser to keep the tool dependency-free; a leading ``---`` block only counts
as frontmatter when it contains at least one ``key:`` line, so a file that
merely opens with a thematic break keeps its body intact.

Known limitation: 4-space-indented code blocks are not masked (only fenced
blocks and inline spans are), and an unclosed inline backtick span is left
as literal text.
"""
from __future__ import annotations

import re

from .model import Page, WikiLink

FENCE_RE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")
# A run of N backticks opens an inline span; the next run of N closes it.
INLINE_CODE_RE = re.compile(r"(`+)[^`]*?\1")
H1_RE = re.compile(r"^\s{0,3}#\s+(.+?)\s*$")
# '!' excluded: ![[X]] embeds are out of scope and must not read as links.
LINK_RE = re.compile(r"(?<!!)\[\[([^\[\]]+)\]\]")
# '#' not preceded by a word char / another '#' / '&' / '/' (URL anchors),
# followed by at least one tag character. Headings ('# Title') have a space
# after '#' and never match.
TAG_RE = re.compile(r"(?<![\w#&/])#([\w/-]+)")
TAG_SHAPE_RE = re.compile(r"[\w-]+(?:/[\w-]+)*")
TAGS_KEY_RE = re.compile(r"^\s*tags\s*:\s*(.*)$", re.IGNORECASE)
LIST_ITEM_RE = re.compile(r"^\s*-\s*(.+?)\s*$")
FM_KEY_RE = re.compile(r"^\s*[\w-]+\s*:")


def split_frontmatter(text: str) -> tuple[str, str, int]:
    """Split an optional ``---`` frontmatter block off the top of *text*.

    Returns ``(frontmatter, body, body_start_line)`` where *body_start_line*
    is the 1-based line number of the first body line. A leading ``---``
    block only counts as frontmatter if it contains at least one ``key:``
    line — a file that opens with a bare thematic break (``---`` ... ``---``)
    keeps its body intact. Text without a well-formed block is returned
    unchanged.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return "", text, 1
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            block = lines[1:i]
            if any(FM_KEY_RE.match(line) for line in block):
                return "\n".join(block), "\n".join(lines[i + 1:]), i + 2
            return "", text, 1  # no key lines: not frontmatter
    return "", text, 1


def mask_code(lines: list[str], start_line: int = 1) -> list[tuple[int, str]]:
    """Blank out fenced code blocks and inline code spans.

    Returns ``(line_number, masked_line)`` pairs. Fenced blocks (`` ``` `` or
    ``~~~``, three or more markers) blank whole lines; inline ``spans``
    collapse to a space so links and tags inside them are never matched.
    """
    masked: list[tuple[int, str]] = []
    fence: tuple[str, int] | None = None  # (marker char, minimum length)
    for offset, line in enumerate(lines):
        lineno = start_line + offset
        marker = FENCE_RE.match(line)
        if fence is None:
            if marker:
                fence = (marker.group(1)[0], len(marker.group(1)))
                masked.append((lineno, ""))
            else:
                masked.append((lineno, INLINE_CODE_RE.sub(" ", line)))
        else:
            if (
                marker
                and marker.group(1)[0] == fence[0]
                and len(marker.group(1)) >= fence[1]
                and line.strip() == marker.group(1)
            ):
                fence = None
            masked.append((lineno, ""))
    return masked


def extract_title(masked: list[tuple[int, str]]) -> str | None:
    """Return the first H1 heading text outside code fences, if any."""
    for _, line in masked:
        m = H1_RE.match(line)
        if m:
            return m.group(1).strip()
    return None


def extract_links(page: Page, masked: list[tuple[int, str]]) -> list[WikiLink]:
    """Pull every ``[[target]]`` (with optional ``|alias``) out of masked lines.

    Embeds (``![[X]]``) never match; same-page anchors (``[[#sec]]``) are not
    page links. The raw text is kept as written — ``WikiLink.target`` strips
    the anchor section for resolution.
    """
    links: list[WikiLink] = []
    for lineno, line in masked:
        for m in LINK_RE.finditer(line):
            text = m.group(1)
            if "|" in text:
                target_part, display_part = text.split("|", 1)
                display = display_part.strip() or None
            else:
                target_part, display = text, None
            raw = target_part.strip()
            if not raw:
                continue
            if not raw.split("#", 1)[0].strip():
                continue  # [[#section]] anchors within the same page
            links.append(WikiLink(page=page, line=lineno, raw=raw, display=display))
    return links


def extract_tags(masked: list[tuple[int, str]]) -> list[tuple[int, str]]:
    """Pull every ``#tag`` occurrence out of masked lines as ``(line, tag)``."""
    hits: list[tuple[int, str]] = []
    for lineno, line in masked:
        for m in TAG_RE.finditer(line):
            tag = m.group(1).rstrip("/")
            if tag and TAG_SHAPE_RE.fullmatch(tag):
                hits.append((lineno, tag))
    return hits


def _split_tag_list(value: str) -> list[str]:
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        value = value[1:-1]
    return [item.strip(" \t'\"") for item in value.split(",") if item.strip(" \t'\"")]


def extract_frontmatter_tags(frontmatter: str) -> list[str]:
    """Line-level parse of ``tags`` from YAML-ish frontmatter.

    Supports ``tags: a, b``, ``tags: [a, b]`` and block lists (``tags:``
    followed by ``- a`` lines). Deliberately not a YAML parser.
    """
    tags: list[str] = []
    in_block = False
    for line in frontmatter.splitlines():
        key = TAGS_KEY_RE.match(line)
        if key:
            rest = key.group(1).strip()
            if rest:
                tags.extend(_split_tag_list(rest))
                in_block = False
            else:
                in_block = True
            continue
        if in_block:
            item = LIST_ITEM_RE.match(line)
            if item:
                tags.extend(_split_tag_list(item.group(1)))
            elif line.strip():
                in_block = False  # a following key ends the list
    return tags
