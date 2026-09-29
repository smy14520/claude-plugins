"""index：Page 集合 → 纯内存索引。

无状态、每命令全量重建（ADR-0001 硬边界：仅纯内存或单文件缓存，
严禁数据库）。本模块不知晓 CLI 与 render。
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from .parse import Page, parse_page
from .resolve import DEAD, AMBIGUOUS, Resolution, resolve_link
from .scan import iter_page_paths, read_text


@dataclass(frozen=True)
class Backlink:
    """一条入向引用：来自其他页面的链接出现处。"""

    source: str  # 引用方相对路径
    line: int  # 1 起行号
    raw: str  # 双括号内原文写法


@dataclass(frozen=True)
class DeadLink:
    """一处死链出现：出处 + 原文写法。"""

    source: str  # 所在页面相对路径
    line: int  # 1 起行号
    raw: str  # 双括号内原文写法


@dataclass(frozen=True)
class AmbiguousLink:
    """一处歧义链接出现：出处 + 原文 + 全部候选页面路径。"""

    source: str  # 所在页面相对路径
    line: int  # 1 起行号
    raw: str  # 双括号内原文写法
    candidates: tuple[str, ...]  # 全部候选页面相对路径


@dataclass(frozen=True)
class DoctorFindings:
    """一次体检的三类发现（doctor 命令的聚合事实）。"""

    dead_links: tuple[DeadLink, ...]
    ambiguous: tuple[AmbiguousLink, ...]
    orphans: tuple[str, ...]  # 孤岛页面相对路径


class VaultIndex:
    """一次命令执行内的全量内存索引。"""

    def __init__(self, pages: Iterable[Page]) -> None:
        self.pages: tuple[Page, ...] = tuple(pages)
        self.by_name: dict[str, list[Page]] = {}
        self.by_path: dict[str, Page] = {}
        for page in self.pages:
            self.by_name.setdefault(page.name, []).append(page)
            self.by_path[page.path.removesuffix(".md")] = page
        self._inbound, self._dead, self._ambiguous = _traverse_links(
            self.pages, self.by_name, self.by_path
        )

    @classmethod
    def from_vault(cls, vault: Path) -> "VaultIndex":
        """扫描 vault 并全量重建索引（scan → parse → index）。"""
        pages = (
            parse_page(read_text(path), path.relative_to(vault).as_posix())
            for path in iter_page_paths(vault)
        )
        return cls(pages)

    def resolve_link(self, target: str) -> Resolution:
        """三态解析一个链接目标（spec 顺序：路径精确 → stem 精确 → 大小写兜底）。

        解析能力内聚在索引上：调用方（cli）只需索引本身，
        不接触 by_name/by_path 内部映射。
        """
        return resolve_link(target, self.by_name, self.by_path)

    def tag_pages(self) -> dict[str, tuple[Page, ...]]:
        """标签 → 打此标签的页面全集（嵌套标签按完整路径聚合）。

        页面按扫描顺序（路径排序）去重列出——单页重复标签只计一页。
        """
        mapping: dict[str, list[Page]] = {}
        for page in self.pages:
            for tag in page.tags:
                mapping.setdefault(tag, []).append(page)
        return {tag: tuple(pages) for tag, pages in mapping.items()}

    def pages_for_tag(self, tag: str) -> tuple[Page, ...]:
        """标签查询 → 页面集合；父标签含全部子孙（`concepts` 命中 `concepts/gc`）。

        同页同时打父子标签只出现一次；结果按扫描顺序（路径排序）。
        """
        pages: dict[str, Page] = {}
        for name, hits in self.tag_pages().items():
            if name == tag or name.startswith(tag + "/"):
                for page in hits:
                    pages[page.path] = page
        return tuple(pages.values())

    def backlinks_for(self, page: Page) -> tuple[Backlink, ...]:
        """指向该页面的全部反向引用（逐条出现处，不合并）。"""
        return self._inbound.get(page.path, ())

    def doctor_findings(self) -> DoctorFindings:
        """三类发现一次聚合：死链接出现处列出、孤岛按路径列出、歧义附全部候选。

        与 `links`/`backlinks` 同源：死链/歧义/入向来自构建时的同一单趟
        resolve 三态遍历（T6），孤岛 = 反向引用为零（自链接不算入向，
        `[[#小节]]` 不产生链接）。
        """
        orphans = tuple(
            page.path for page in self.pages if not self._inbound.get(page.path)
        )
        return DoctorFindings(
            dead_links=self._dead, ambiguous=self._ambiguous, orphans=orphans
        )


def _traverse_links(
    pages: Sequence[Page],
    by_name: Mapping[str, Sequence[Page]],
    by_path: Mapping[str, Page],
) -> tuple[dict[str, tuple[Backlink, ...]], tuple[DeadLink, ...], tuple[AmbiguousLink, ...]]:
    """单趟遍历：链接出现处 × 三态解析 → 入向索引 + 死链/歧义发现。

    backlinks（入向）与 doctor（三类发现）同源复用这一遍结果；
    歧义链接记入每个候选页面；自链接（引用方 == 目标）不构成反向引用。
    """
    inbound: dict[str, list[Backlink]] = {}
    dead: list[DeadLink] = []
    ambiguous: list[AmbiguousLink] = []
    for page in pages:
        for link in page.links:
            resolution = resolve_link(link.target, by_name, by_path)
            if resolution.status == DEAD:
                dead.append(DeadLink(page.path, link.line, link.raw))
            elif resolution.status == AMBIGUOUS:
                ambiguous.append(
                    AmbiguousLink(
                        page.path,
                        link.line,
                        link.raw,
                        tuple(p.path for p in resolution.targets),
                    )
                )
            for target in resolution.targets:
                if target.path == page.path:
                    continue
                inbound.setdefault(target.path, []).append(
                    Backlink(source=page.path, line=link.line, raw=link.raw)
                )
    return (
        {path: tuple(entries) for path, entries in inbound.items()},
        tuple(dead),
        tuple(ambiguous),
    )
