"""LinkGraph：Vault 级装配器。

负责文件发现（递归，跳过隐藏目录）、页面名注册表（NFC 归一 + casefold）、
链接目标到 Page 的解析与全 Vault 出边表。依赖 Parser，不依赖任何检索设施；
每次命令全量扫描、索引仅存内存（ADR-0002），无任何持久化。
"""

from __future__ import annotations

import os
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from wiki_cli.parser import parse_markdown

PAGE_SUFFIX = ".md"


def normalize_name(text: str) -> str:
    """页面身份归一：Unicode NFC 归一（防 macOS NFD 形态不等价）+ casefold。"""
    return unicodedata.normalize("NFC", text).casefold()


def display_ref(rel_path: str) -> str:
    """Page 的展示 / JSON 引用形态：相对路径去 .md，统一 NFC。"""
    stem = rel_path.removesuffix(PAGE_SUFFIX)
    return unicodedata.normalize("NFC", stem)


@dataclass(frozen=True)
class PageRef:
    """Vault 内一个 Page：页面名 = 文件名去 .md 后缀。"""

    name: str  # 页面名（保留文件系统中的原始写法）
    rel_path: str  # 相对 Vault 根的 POSIX 路径（含 .md）

    @property
    def ref(self) -> str:
        """展示 / JSON 引用形态（如 `子目录/名`）。"""
        return display_ref(self.rel_path)


@dataclass(frozen=True)
class LinkEntry:
    """一条 Link 的 Vault 级视图：来源 Page、目标写法与解析结果。"""

    source: PageRef
    target: str  # 剥离别名 / 锚点后的原始目标写法
    line: int  # 1 起算的行号
    resolved: PageRef | None  # None = 解析失败（死链候选，或同名冲突不静默任选）


def discover_pages(vault: Path) -> list[PageRef]:
    """递归发现 Vault 内全部 Page（.md），跳过隐藏目录与隐藏文件。

    按相对路径排序，保证发现顺序稳定（输出与测试可复现）。
    """
    pages: list[PageRef] = []
    for dirpath, dirnames, filenames in os.walk(vault):
        dirnames[:] = sorted(name for name in dirnames if not name.startswith("."))
        for filename in sorted(filenames):
            if filename.startswith(".") or not filename.endswith(PAGE_SUFFIX):
                continue
            rel_path = Path(dirpath, filename).relative_to(vault).as_posix()
            pages.append(PageRef(name=filename.removesuffix(PAGE_SUFFIX), rel_path=rel_path))
    return pages


class PageRegistry:
    """页面名注册表：归一键 → Page，供链接目标与页面参数查询。"""

    def __init__(self, pages: list[PageRef]):
        self.pages = pages
        self._by_name: dict[str, list[PageRef]] = {}
        self._by_rel_stem: dict[str, PageRef] = {}
        for page in pages:
            self._by_name.setdefault(normalize_name(page.name), []).append(page)
            self._by_rel_stem[normalize_name(display_ref(page.rel_path))] = page

    def resolve(self, target: str) -> PageRef | None:
        """把链接目标解析为 Page。

        `子目录/名` 形态先按相对路径精确匹配；否则按页面名（basename）全局匹配。
        casefold 后命中多个同名 Page 时不静默任选，返回 None（冲突由 doctor 报告）。
        """
        key = normalize_name(target)
        exact = self._by_rel_stem.get(key)
        if exact is not None:
            return exact
        candidates = self._by_name.get(key, [])
        if len(candidates) == 1:
            return candidates[0]
        return None  # 0 个 = 死链候选；多于 1 个 = 页面名冲突，不静默任选

    def find(self, page_arg: str) -> PageRef | None:
        """按用户给出的页面名查 Page；兼容带 .md 后缀的写法。"""
        page = self.resolve(page_arg)
        if page is not None:
            return page
        stripped = page_arg.strip()
        if stripped.lower().endswith(PAGE_SUFFIX):
            return self.resolve(stripped[: -len(PAGE_SUFFIX)])
        return None


class LinkGraph:
    """全 Vault 链接图：一次全量扫描构建，仅存内存。"""

    def __init__(self, vault: Path):
        self.vault = vault
        self.pages = discover_pages(vault)
        self.registry = PageRegistry(self.pages)
        self.entries: list[LinkEntry] = []
        for page in self.pages:
            text = (vault / page.rel_path).read_text(encoding="utf-8", errors="replace")
            for link in parse_markdown(text).links:
                self.entries.append(
                    LinkEntry(
                        source=page,
                        target=link.target,
                        line=link.line,
                        resolved=self.registry.resolve(link.target),
                    )
                )

    def find_page(self, page_arg: str) -> PageRef | None:
        return self.registry.find(page_arg)

    def links_of(self, page: PageRef) -> list[LinkEntry]:
        """某页的全部出链（构建时已按 Page 与行号排序）。"""
        return [entry for entry in self.entries if entry.source == page]

    def pages_with_links(self) -> list[tuple[PageRef, list[LinkEntry]]]:
        """按 Page 分组的出边表，只含有出链的 Page，顺序稳定。"""
        grouped: list[tuple[PageRef, list[LinkEntry]]] = []
        for page in self.pages:
            entries = self.links_of(page)
            if entries:
                grouped.append((page, entries))
        return grouped
