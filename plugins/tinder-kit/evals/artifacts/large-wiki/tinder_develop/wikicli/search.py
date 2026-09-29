"""search：关键词全文检索（ticket 05）。

语义（spec）：多关键词 AND；大小写不敏感子串匹配（无分词，CJK 友好）；
标题命中 = 页面名/H1/frontmatter title 任一包含；排序：标题命中 >
内容出现频次 > 路径字典序；每页至多 3 条命中行（行号 + 截断行文本）。

匹配作用于剥离代码区后的正文（代码区不算命中），行号建在
`strip_code` 保留的行结构上——与 links/backlinks 的行号约定一致
（frontmatter 剥离后的正文相对行号）。
纯内存全量重扫（ADR-0001）：scan → parse → 匹配排序，无任何持久化。
本模块不知晓 CLI 与 render。
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from .parse import parse_page, split_frontmatter, strip_code
from .scan import iter_page_paths, read_text

#: 每页最多展示的命中行数
MAX_HIT_LINES = 3
#: 命中行文本最大长度（超出截断，以 … 收尾）
MAX_LINE_LEN = 80

_H1_RE = re.compile(r"^ {0,3}#\s+(.+)$")


@dataclass(frozen=True)
class SearchHit:
    """一条命中行：正文相对行号 + 截断后的行文本。"""

    line: int
    text: str


@dataclass(frozen=True)
class SearchMatch:
    """一个命中页面的排序视图。"""

    path: str  # vault 相对路径（posix 分隔）
    name: str  # 页面名 = 文件名 stem
    title_hit: bool  # 全部关键词都出现在标题面（页面名/H1/title）
    frequency: int  # 各关键词在剥码正文的出现次数之和
    hits: tuple[SearchHit, ...]  # 至多 MAX_HIT_LINES 条，按行号


@dataclass(frozen=True)
class SearchResult:
    """`search <kw...>` 的查询结果；matches 已按契约排序。"""

    keywords: tuple[str, ...]
    matches: tuple[SearchMatch, ...]


def search_vault(vault: Path, keywords: Sequence[str]) -> SearchResult:
    """全量重扫 vault，多关键词 AND 检索并按契约排序。"""
    keys = [kw.casefold() for kw in keywords]
    matches: list[SearchMatch] = []
    for path in iter_page_paths(vault):
        text = read_text(path)
        rel_path = path.relative_to(vault).as_posix()
        page = parse_page(text, rel_path)
        body, _ = split_frontmatter(text)
        lines = strip_code(body).split("\n")
        folded_lines = [line.casefold() for line in lines]

        # 标题面：页面名 / H1 / frontmatter title（大小写不敏感）
        name = page.name.casefold()
        h1 = next((m.group(1) for line in lines if (m := _H1_RE.match(line))), "")
        h1 = h1.casefold()
        front_title = (page.title or "").casefold()
        title_surfaces = (name, h1, front_title)

        def in_title(kw: str) -> bool:
            return any(kw in surface for surface in title_surfaces)

        body_blob = "\n".join(folded_lines)
        # AND：每个关键词都出现在正文或标题面
        if not all(kw in body_blob or in_title(kw) for kw in keys):
            continue
        title_hit = all(in_title(kw) for kw in keys)
        frequency = sum(folded.count(kw) for folded in folded_lines for kw in keys)

        # 命中行：含全部关键词的行优先且必须入选（全关键词行本身超过
        # MAX_HIT_LINES 时取行号靠前的），剩余名额由含任一关键词的行
        # 按行号补足；展示按行号（去重天然成立）。
        all_kw_lines = [
            lineno
            for lineno, folded in enumerate(folded_lines, 1)
            if all(kw in folded for kw in keys)
        ]
        selected = set(all_kw_lines[:MAX_HIT_LINES])
        for lineno, folded in enumerate(folded_lines, 1):
            if len(selected) == MAX_HIT_LINES:
                break
            if lineno not in selected and any(kw in folded for kw in keys):
                selected.add(lineno)
        hits = [
            SearchHit(line=lineno, text=_truncate(lines[lineno - 1]))
            for lineno in sorted(selected)
        ]
        matches.append(
            SearchMatch(
                path=rel_path,
                name=page.name,
                title_hit=title_hit,
                frequency=frequency,
                hits=tuple(hits),
            )
        )
    matches.sort(key=lambda m: (not m.title_hit, -m.frequency, m.path))
    return SearchResult(keywords=tuple(keywords), matches=tuple(matches))


def _truncate(line: str) -> str:
    if len(line) <= MAX_LINE_LEN:
        return line
    return line[: MAX_LINE_LEN - 1] + "…"
