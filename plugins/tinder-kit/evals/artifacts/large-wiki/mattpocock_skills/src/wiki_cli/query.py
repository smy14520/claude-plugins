"""查询层：反向引用、出链、标签聚合、全文检索。

检索不依赖索引里的正文（索引不存正文，见 ADR-0002）：按索引的页面清单
流式现读文件做子串 AND 匹配。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .model import Index, Page, WikiLink
from .parser import split_frontmatter, read_lines

SNIPPET_WIDTH = 60


@dataclass(frozen=True)
class LinkStatus:
    """一条链接相对当前 Vault 的状态。歧义 = 目标命中多个重名页。"""

    RESOLVED = "resolved"
    DEAD = "dead"
    EXTERNAL = "external"
    AMBIGUOUS = "ambiguous"


def resolve_target(index: Index, target: str) -> tuple[str, list[Page]]:
    """解析链接目标，返回 (状态, 命中的页面列表)。

    重名目标不参与解析（ADR-0001：重名页不可解析为单一目标），
    其根因由体检的重名缺陷暴露，这里不二次报死链。
    """
    matches = index.by_name().get(target, [])
    if not matches:
        return LinkStatus.DEAD, []
    if len(matches) > 1:
        return LinkStatus.AMBIGUOUS, matches
    return LinkStatus.RESOLVED, matches


def backlinks(index: Index, name: str) -> list[tuple[Page, WikiLink]]:
    """指向 name 的全部入链，按 (来源路径, 行号) 排序。"""
    result: list[tuple[Page, WikiLink]] = []
    for page in index.pages:
        for link in page.links:
            if not link.external and link.target == name:
                result.append((page, link))
    result.sort(key=lambda pair: (pair[0].rel_path, pair[1].line))
    return result


def outlinks(page: Page) -> list[WikiLink]:
    return sorted(page.links, key=lambda link: link.line)


def tag_pages(index: Index, tag: str) -> list[Page]:
    """打了某标签的全部页面，按相对路径排序。"""
    return sorted(
        (p for p in index.pages if tag in p.tags),
        key=lambda p: p.rel_path,
    )


def tag_counts(index: Index) -> list[tuple[str, int]]:
    """标签 → 打了它的页面数（两处来源合并去重后），按 (计数降序, 标签名) 排序。"""
    by_tag = index.by_tag()
    return sorted(
        ((tag, len(pages)) for tag, pages in by_tag.items()),
        key=lambda pair: (-pair[1], pair[0]),
    )


@dataclass(frozen=True)
class SearchHit:
    page: Page
    identity_hit: bool
    count: int
    snippet: str


def _snippet(body_lines: list[str], terms: list[str]) -> str:
    """第一条包含任一关键词的正文行，截窗口展示。"""
    for line in body_lines:
        folded = line.casefold()
        for term in terms:
            idx = folded.find(term)
            if idx >= 0:
                start = max(0, idx - 15)
                end = min(len(line), idx + SNIPPET_WIDTH)
                prefix = "…" if start > 0 else ""
                suffix = "…" if end < len(line) else ""
                return prefix + line[start:end].strip() + suffix
    return ""


def search(index: Index, root: Path, terms: list[str]) -> list[SearchHit]:
    """全文检索：页面身份与正文（frontmatter 剥离后）的子串 AND 匹配。

    排序：身份命中优先，其后按正文命中总数降序，再按页面名稳定排序。
    Latin 侧大小写不敏感（casefold），中文不受影响。
    """
    folded_terms = [t.casefold() for t in terms]
    hits: list[SearchHit] = []
    for page in index.pages:
        lines = read_lines(root / page.rel_path)
        body_lines = split_frontmatter(lines)[1]
        folded_body = "\n".join(body_lines).casefold()
        per_term = [folded_body.count(t) for t in folded_terms]
        identity_hit = all(t in page.name.casefold() for t in folded_terms)
        body_hit = all(c > 0 for c in per_term)
        if not (identity_hit or body_hit):
            continue
        hits.append(
            SearchHit(
                page=page,
                identity_hit=identity_hit,
                count=sum(per_term),
                snippet=_snippet(body_lines, folded_terms) if body_hit else "",
            )
        )
    hits.sort(key=lambda h: (not h.identity_hit, -h.count, h.page.name))
    return hits
