"""核心数据模型：Index 深模块（构建与查询的公共数据契约）。

postings（token → {PageName: tf}）的表示细节仅在本包内使用，
对外查询能力由 Index 的方法暴露（ADR-0003）。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .parser import Link
from .tokenize import tokenize

_TAG_PART_RE = re.compile(r"[^./]+")


def _tag_prefixes(tag: str) -> list[str]:
    """`lang/python` → [`lang`, `lang/python`]（按原文切点取前缀）。"""
    return [tag[:match.end()] for match in _TAG_PART_RE.finditer(tag)]


@dataclass(frozen=True)
class SearchHit:
    """一条检索结果：页面名与 TF 累计得分（摘要属 CLI 渲染路径，见 ADR-0004 修订）。"""

    page: str
    score: int


@dataclass(frozen=True)
class PageInfo:
    """单页的索引记录：物理位置、构建时的 stat 指纹、词法产物。"""

    file: str  # vault 相对路径（posix）
    mtime: float
    size: int
    links: list[Link]
    tags: list[str]


@dataclass
class Index:
    """全库索引：页面记录 + 倒排表。查询命令只读此结构（ADR-0004）。"""

    version: int = 1
    pages: dict[str, PageInfo] = field(default_factory=dict)
    postings: dict[str, dict[str, int]] = field(default_factory=dict)

    def resolve(self, page: str) -> str | None:
        """PageName 大小写不敏感归一（ADR-0001）；不存在返回 None。"""
        fold = page.strip().casefold()
        return next((name for name in self.pages if name.casefold() == fold), None)

    def backlinks(self, page: str) -> list[str]:
        """指向该页（大小写不敏感）的全部来源页，按名称排序。"""
        fold = page.strip().casefold()
        sources = {
            name
            for name, info in self.pages.items()
            for link in info.links
            if link.target.strip().casefold() == fold
        }
        return sorted(sources)

    def tag_counts(self) -> dict[str, int]:
        """标签 → 页面数；父标签聚合全部子孙标签（每页每前缀计一次）。"""
        counts: dict[str, int] = {}
        for info in self.pages.values():
            for prefix in {p for tag in info.tags for p in _tag_prefixes(tag)}:
                counts[prefix] = counts.get(prefix, 0) + 1
        return counts

    def pages_under_tag(self, tag: str) -> list[str]:
        """拥有该标签或其子孙标签的页面，按名称排序。"""
        wanted = tag.strip()
        under = [
            name
            for name, info in self.pages.items()
            if any(
                t == wanted
                or (t.startswith(wanted) and len(t) > len(wanted) and t[len(wanted)] in "./")
                for t in info.tags
            )
        ]
        return sorted(under)

    def search(self, query: str) -> list[SearchHit]:
        """倒排求交（AND）+ TF 累计计分，按 (-score, page) 排序（ADR-0003）。

        只读索引，绝不触碰 vault 文件（ADR-0004 修订）。
        """
        tokens = tokenize(query)
        if not tokens:
            return []

        candidate: set[str] | None = None
        for token in tokens:
            hits = self.postings.get(token)
            if not hits:
                return []
            pages = set(hits)
            candidate = pages if candidate is None else candidate & pages
            if not candidate:
                return []

        scored = sorted(
            (
                (sum(self.postings[t].get(name, 0) for t in tokens), name)
                for name in candidate
            ),
            key=lambda item: (-item[0], item[1]),
        )
        return [SearchHit(page=name, score=score) for score, name in scored]
