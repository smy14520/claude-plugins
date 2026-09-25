"""核心领域对象：页面与索引（术语见 .forge/CONTEXT.md）。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class Page:
    """页面：身份 = 文件名去 .md，大小写敏感（ADR-0003）。"""

    title: str
    path: str  # 相对知识库根目录的 posix 路径
    links: list[str]  # 出链目标，排序去重
    tags: list[str]  # 小写归一、排序去重
    body: str  # 正文（frontmatter 已剥离）；仅内存检索使用，不落盘


@dataclass
class WikiIndex:
    """索引：可整体丢弃重建的派生数据（ADR-0001），绝非真实源。"""

    root: Path
    pages: list[Page]  # 按 (title, path) 排序

    def title_map(self) -> dict[str, list[Page]]:
        """页面名 → 同名页面列表；重复标题全部保留（歧义由 doctor 上报）。"""
        mapping: dict[str, list[Page]] = {}
        for page in self.pages:
            mapping.setdefault(page.title, []).append(page)
        return mapping
