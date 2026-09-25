"""词法扫描：从 Markdown 正文提取 WikiLink 与 Tag。

排除规则（CONTEXT.md 中 Tag/WikiLink 词条的实现）：
- fenced code block（``` 或 ~~~）内的内容整体跳过；
- 行内代码 `` `...` `` 先移除，再扫描链接与标签；
- ATX 标题记号 `#{1,6}` + 空格不构成标签（正则形状天然排除），
  标题行内的 `#标签` 仍计数；
- `#` 紧跟 `#`（如 `##tag`）不算标签；
- URL（`scheme://...`）整体移除，其 `#anchor` 不产生标签。
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_FENCE_RE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")
_INLINE_CODE_RE = re.compile(r"`+[^`]*`+")
_URL_RE = re.compile(r"[A-Za-z][A-Za-z0-9+.\-]*://\S*")
_WIKILINK_RE = re.compile(r"\[\[([^\[\]|]*?)(?:\|([^\[\]]*))?\]\]")
_TAG_RE = re.compile(r"#(\w[\w./]*)")


@dataclass(frozen=True)
class Link:
    """一条 WikiLink：目标页面名（strip 后，保留原大小写）与 1-based 行号。"""

    target: str
    line: int


@dataclass(frozen=True)
class PageScan:
    """单页扫描结果。tags 已按出现顺序去重。"""

    links: list[Link]
    tags: list[str]


def scan_page(text: str) -> PageScan:
    links: list[Link] = []
    tags: list[str] = []
    fence_char: str | None = None

    for lineno, raw in enumerate(text.splitlines(), 1):
        fence_match = _FENCE_RE.match(raw)
        if fence_match:
            marker = fence_match.group(1)
            if fence_char is None:
                fence_char = marker[0]
            elif marker[0] == fence_char:
                fence_char = None
            continue
        if fence_char:
            continue

        prose = _INLINE_CODE_RE.sub(" ", raw)

        for match in _WIKILINK_RE.finditer(prose):
            target = match.group(1).strip()
            if target:
                links.append(Link(target=target, line=lineno))

        prose = _URL_RE.sub(" ", prose)
        for match in _TAG_RE.finditer(prose):
            if match.start() > 0 and prose[match.start() - 1] == "#":
                continue
            tag = match.group(1).rstrip("./")
            if tag and tag not in tags:
                tags.append(tag)

    return PageScan(links=links, tags=tags)
