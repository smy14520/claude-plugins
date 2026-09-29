"""render：查询结果 → 人读文本 | JSON（`--json` 双模式）。

契约：每条命令产出一个结果对象（LinksResult 等），人读与 JSON 两个
渲染函数消费同一对象——输出模式的分叉点只在这里，不在别处。
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from .index import AmbiguousLink, Backlink, DeadLink
from .resolve import AMBIGUOUS, RESOLVED
from .search import SearchResult


@dataclass(frozen=True)
class LinkEntry:
    """`links` 输出里的一条链接行。"""

    raw: str  # 双括号内原文写法
    status: str  # resolved / dead / ambiguous
    target: str | None  # 解析命中时的目标相对路径；未唯一命中为 None
    candidates: tuple[str, ...] = ()  # 歧义时的全部候选路径（仅人读格式展示）


@dataclass(frozen=True)
class LinksResult:
    """`links <page>` 的查询结果。"""

    page_path: str
    page_name: str
    entries: tuple[LinkEntry, ...]


@dataclass(frozen=True)
class BacklinksResult:
    """`backlinks <page>` 的查询结果（条目复用 index 侧 Backlink）。"""

    page_path: str
    page_name: str
    entries: tuple[Backlink, ...]


def _occurrence_line(entry: Backlink | DeadLink) -> str:
    """链接出现处的统一行形态：`出处:行号  [[原文]]`（backlinks 与死链块共用）。"""
    return f"{entry.source}:{entry.line}  [[{entry.raw}]]"


def backlinks_human(result: BacklinksResult) -> str:
    """人读文本：头行 + 逐条反向引用行。"""
    lines = [
        f"{result.page_path} ({result.page_name}) ← {len(result.entries)} 条反向引用"
    ]
    lines.extend(_occurrence_line(entry) for entry in result.entries)
    return "\n".join(lines) + "\n"


def backlinks_json(result: BacklinksResult) -> str:
    """`--json` 文档：单个 JSON 对象，字段名稳定。"""
    doc = {
        "command": "backlinks",
        "page": {"path": result.page_path, "name": result.page_name},
        "backlinks": [
            {"source": e.source, "line": e.line, "raw": e.raw}
            for e in result.entries
        ],
    }
    return json.dumps(doc, ensure_ascii=False, indent=2) + "\n"


def links_human(result: LinksResult) -> str:
    """人读文本：头行 + 逐条链接行。"""
    lines = [f"{result.page_path} ({result.page_name})"]
    for entry in result.entries:
        if entry.status == RESOLVED:
            lines.append(f"→ {entry.target}  [[{entry.raw}]]")
        elif entry.status == AMBIGUOUS:
            lines.append(f"⚠ 歧义: [[{entry.raw}]] → {', '.join(entry.candidates)}")
        else:
            lines.append(f"✗ 未解析: [[{entry.raw}]]")
    return "\n".join(lines) + "\n"


def links_json(result: LinksResult) -> str:
    """`--json` 文档：单个 JSON 对象，字段名稳定。"""
    doc = {
        "command": "links",
        "page": {"path": result.page_path, "name": result.page_name},
        "links": [
            {"raw": e.raw, "status": e.status, "target": e.target}
            for e in result.entries
        ],
    }
    return json.dumps(doc, ensure_ascii=False, indent=2) + "\n"


@dataclass(frozen=True)
class TagCount:
    """标签聚合视图里的一行：标签名 + 覆盖页数。"""

    tag: str
    page_count: int


@dataclass(frozen=True)
class TagsOverviewResult:
    """`tags`（无参）的全库聚合结果；条目已按 render 契约排序。"""

    tags: tuple[TagCount, ...]


def tags_human(result: TagsOverviewResult) -> str:
    """人读文本：`#标签名  N 页` 逐行。"""
    return "".join(f"#{t.tag}  {t.page_count} 页\n" for t in result.tags)


@dataclass(frozen=True)
class TagPagesResult:
    """`tags <tag>` 的查询结果：标签 → 页面路径列表。"""

    tag: str
    pages: tuple[str, ...]  # 页面相对路径，按扫描顺序（路径排序）


def tag_pages_human(result: TagPagesResult) -> str:
    """人读文本：页面路径逐行列出。"""
    return "".join(f"{path}\n" for path in result.pages)


def tags_json(result: TagsOverviewResult) -> str:
    """`--json` 文档：单个 JSON 对象，字段名稳定。"""
    doc = {
        "command": "tags",
        "tags": [
            {"tag": t.tag, "page_count": t.page_count} for t in result.tags
        ],
    }
    return json.dumps(doc, ensure_ascii=False, indent=2) + "\n"


def tag_pages_json(result: TagPagesResult) -> str:
    """`--json` 文档：单个 JSON 对象，字段名稳定。"""
    doc = {
        "command": "tags",
        "tag": result.tag,
        "pages": list(result.pages),
    }
    return json.dumps(doc, ensure_ascii=False, indent=2) + "\n"


def search_human(result: SearchResult) -> str:
    """人读文本：`N 个页面命中 · 关键词: …` 头行 + 每页命中块（render 契约）。"""
    lines = [f"{len(result.matches)} 个页面命中 · 关键词: {' '.join(result.keywords)}"]
    for i, match in enumerate(result.matches, 1):
        kind = "标题命中" if match.title_hit else f"内容 ×{match.frequency}"
        lines.append(f"{i}. {match.path}  {kind}")
        for hit in match.hits:
            lines.append(f"    {hit.line}: {hit.text}")
    return "\n".join(lines) + "\n"


def search_json(result: SearchResult) -> str:
    """`--json` 文档：单个 JSON 对象，字段名稳定（只加不改）。"""
    doc = {
        "command": "search",
        "keywords": list(result.keywords),
        "page_count": len(result.matches),
        "matches": [
            {
                "path": m.path,
                "name": m.name,
                "title_hit": m.title_hit,
                "frequency": m.frequency,
                "lines": [{"line": h.line, "text": h.text} for h in m.hits],
            }
            for m in result.matches
        ],
    }
    return json.dumps(doc, ensure_ascii=False, indent=2) + "\n"


@dataclass(frozen=True)
class DoctorResult:
    """`doctor` 的体检结果：统计行数字 + 三类发现（条目复用 index 侧类型）。"""

    page_count: int
    link_count: int  # 全库链接出现次数（`[[#小节]]` 不计）
    tag_count: int  # 去重后的标签数
    dead_links: tuple[DeadLink, ...]
    orphans: tuple[str, ...]  # 孤岛页面相对路径
    ambiguous: tuple[AmbiguousLink, ...]


def doctor_json(result: DoctorResult) -> str:
    """`--json` 文档：单个 JSON 对象，字段名稳定（与 DoctorResult 一一对应）。"""
    doc = {
        "command": "doctor",
        "page_count": result.page_count,
        "link_count": result.link_count,
        "tag_count": result.tag_count,
        "dead_links": [
            {"source": e.source, "line": e.line, "raw": e.raw}
            for e in result.dead_links
        ],
        "orphans": list(result.orphans),
        "ambiguous": [
            {
                "source": e.source,
                "line": e.line,
                "raw": e.raw,
                "candidates": list(e.candidates),
            }
            for e in result.ambiguous
        ],
    }
    return json.dumps(doc, ensure_ascii=False, indent=2) + "\n"


def doctor_human(result: DoctorResult) -> str:
    """人读文本：统计行 + `✗ 死链` 块 + `⚠ 孤岛页面` 块 + `歧义链接` 块。

    无发现的块整块省略——零发现的 vault 只剩统计行。
    """
    lines = [
        f"体检: {result.page_count} 页面"
        f" · {result.link_count} 条链接"
        f" · {result.tag_count} 个标签"
    ]
    if result.dead_links:
        lines.append("✗ 死链")
        lines.extend(_occurrence_line(e) for e in result.dead_links)
    if result.orphans:
        lines.append("⚠ 孤岛页面")
        lines.extend(result.orphans)
    if result.ambiguous:
        lines.append("歧义链接")
        lines.extend(
            f"{e.source}:{e.line}  ⚠ 歧义: [[{e.raw}]] → {', '.join(e.candidates)}"
            for e in result.ambiguous
        )
    return "\n".join(lines) + "\n"
