"""核心域模型。术语以根目录 CONTEXT.md 为准。"""

from __future__ import annotations

from dataclasses import dataclass

INDEX_VERSION = 1
INDEX_FILENAME = ".wiki_index.json"
MD_SUFFIX = ".md"


@dataclass(frozen=True)
class WikiLink:
    """一条解析后的 wikilink。

    target: 剥离锚点与末尾 ``.md`` 后缀后的链接目标；外部链接时为原始文本。
    raw:    用户书写的目标原文（别名与锚点剥离前），用于报告展示。
    """

    target: str
    raw: str
    line: int
    alias: str | None = None
    anchor: str | None = None
    embed: bool = False
    external: bool = False


@dataclass(frozen=True)
class Page:
    """Vault 内一个 ``.md`` 文件。

    name 即页面身份：文件名去掉末尾 ``.md``，全 Vault 唯一；重名是缺陷，
    由体检暴露，解析器不静默择一。
    """

    name: str
    rel_path: str
    size: int
    mtime_ns: int
    tags: tuple[str, ...]
    links: tuple[WikiLink, ...]
    malformed_frontmatter: bool = False


@dataclass(frozen=True)
class Index:
    """Vault 的派生缓存。文件系统是唯一真相，索引随时可丢弃重建。"""

    version: int
    pages: tuple[Page, ...]

    def by_name(self) -> dict[str, list[Page]]:
        """身份 → 页面列表。列表长度大于 1 即重名缺陷。"""
        by_name: dict[str, list[Page]] = {}
        for page in self.pages:
            by_name.setdefault(page.name, []).append(page)
        return by_name

    def by_tag(self) -> dict[str, set[str]]:
        """标签 → 指向它的页面身份集合（两处来源合并去重后的结果）。"""
        by_tag: dict[str, set[str]] = {}
        for page in self.pages:
            for tag in page.tags:
                by_tag.setdefault(tag, set()).add(page.name)
        return by_tag
