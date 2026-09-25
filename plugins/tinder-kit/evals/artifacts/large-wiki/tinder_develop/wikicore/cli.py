"""wiki-cli 薄壳：参数解析、渲染与退出码。

所有逻辑在 wikicore 内核；本模块只做 IO 与格式化。
检索命中摘要（build_snippet）属渲染路径，在此层读取命中页原文（ADR-0004 修订）。
退出码：0 正常/体检干净；1 操作失败或体检发现问题。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from .health import check
from .indexer import (
    INDEX_NAME,
    DuplicatePageError,
    IndexNotFound,
    build_index,
    index_out_of_date,
    load_index,
    save_index,
)
from .tokenize import tokenize

_SNIPPET_WIDTH = 30


class CommandError(Exception):
    """面向用户的操作失败（页面不存在等），退出码 1。"""


def build_snippet(text: str, tokens: list[str], width: int = _SNIPPET_WIDTH) -> str:
    """渲染路径：从原文截取首个命中附近的窗口；无命中退化为开头一段。

    在原文上做 IGNORECASE 检索，偏移量天然对齐（规避 casefold 变长的错位）。
    """
    positions = []
    for token in tokens:
        found = re.search(re.escape(token), text, re.IGNORECASE)
        if found:
            positions.append(found.start())
    if not positions:
        return text.strip()[:width]

    first = min(positions)
    start = max(0, first - width // 2)
    end = min(len(text), first + max(len(t) for t in tokens) + width // 2)
    prefix = "…" if start > 0 else ""
    suffix = "…" if end < len(text) else ""
    return f"{prefix}{text[start:end].strip()}{suffix}"


def _cmd_build(args) -> int:
    root = Path(args.root)
    previous = load_index(root) if (root / INDEX_NAME).is_file() else None
    index = build_index(root, previous)
    save_index(index, root)

    total = len(index.pages)
    if previous is None:
        added, updated, deleted = total, 0, 0
    else:
        added = sum(1 for name in index.pages if name not in previous.pages)
        updated = sum(
            1 for name, info in index.pages.items()
            if name in previous.pages and previous.pages[name] is not info
        )
        deleted = sum(1 for name in previous.pages if name not in index.pages)

    _emit(
        args.json,
        {"pages": total, "new": added, "updated": updated, "deleted": deleted},
        [f"已索引 {total} 个页面（新增 {added}，更新 {updated}，删除 {deleted}）"],
    )
    return 0


def _cmd_links(args) -> int:
    index = _require_index(Path(args.root))
    page = _resolve_or_fail(index, args.page)
    links = index.pages[page].links
    _emit(
        args.json,
        [{"target": link.target, "line": link.line} for link in links],
        [link.target for link in links],
    )
    return 0


def _cmd_backlinks(args) -> int:
    index = _require_index(Path(args.root))
    page = _resolve_or_fail(index, args.page)
    names = index.backlinks(page)
    _emit(args.json, names, names)
    return 0


def _cmd_tags(args) -> int:
    index = _require_index(Path(args.root))
    if args.tag is None:
        counts = index.tag_counts()
        _emit(
            args.json,
            counts,
            [
                f"{count:4d}  {tag}"
                for tag, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
            ],
        )
        return 0
    names = index.pages_under_tag(args.tag)
    _emit(args.json, names, names)
    return 0


def _cmd_search(args) -> int:
    root = Path(args.root)
    index = _require_index(root)
    query = " ".join(args.query)
    hits = index.search(query)
    tokens = tokenize(query)
    rows = [
        {
            "page": hit.page,
            "score": hit.score,
            "snippet": build_snippet(_page_text(root, index.pages[hit.page].file), tokens),
        }
        for hit in hits
    ]
    if args.json:
        _dump_json(rows)
        return 0
    for rank, row in enumerate(rows, 1):
        print(f"{rank}. {row['page']}（得分 {row['score']}）")
        print(f"   {row['snippet']}")
    return 0


def _cmd_doctor(args) -> int:
    index = _require_index(Path(args.root))
    report = check(index, entries=args.entry)
    dead_links = [
        {"page": d.page, "line": d.line, "target": d.target} for d in report.dead_links
    ]
    healthy = not dead_links and not report.orphans

    if args.json:
        _dump_json({"healthy": healthy, "dead_links": dead_links, "orphans": report.orphans})
        return 0 if healthy else 1

    if healthy:
        print("体检通过：无死链、无孤岛页面。")
        return 0
    if dead_links:
        print(f"死链 ({len(dead_links)}):")
        for d in dead_links:
            print(f"  {d['page']}.md:{d['line']} → {d['target']}")
    if report.orphans:
        print(f"孤岛页面 ({len(report.orphans)}):")
        for name in report.orphans:
            print(f"  {name}")
    return 1


def _build_parser() -> argparse.ArgumentParser:
    main_common = argparse.ArgumentParser(add_help=False)
    main_common.add_argument("--root", default=".", help="Vault 根目录（缺省当前目录）")
    main_common.add_argument("--json", action="store_true", help="以 JSON 输出")

    # 子解析器的同名选项以 SUPPRESS 为缺省：未显式传入时不回写，
    # 避免覆盖主解析器在子命令之前解析到的值
    sub_common = argparse.ArgumentParser(add_help=False)
    sub_common.add_argument("--root", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    sub_common.add_argument(
        "--json", action="store_true", default=argparse.SUPPRESS, help=argparse.SUPPRESS
    )

    parser = argparse.ArgumentParser(
        prog="wiki-cli", description="本地 Markdown 个人 Wiki 知识库管理内核",
        parents=[main_common],
    )
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build", parents=[sub_common], help="构建/增量更新索引")
    build.set_defaults(func=_cmd_build)

    for name, func, help_text in (
        ("links", _cmd_links, "列出页面的出链"),
        ("backlinks", _cmd_backlinks, "列出页面的入链（反向引用）"),
    ):
        p = sub.add_parser(name, parents=[sub_common], help=help_text)
        p.add_argument("page", help="页面名（大小写不敏感）")
        p.set_defaults(func=func)

    tags = sub.add_parser("tags", parents=[sub_common], help="标签聚合；带标签名则列出页面")
    tags.add_argument("tag", nargs="?", default=None)
    tags.set_defaults(func=_cmd_tags)

    search = sub.add_parser("search", parents=[sub_common], help="全文检索")
    search.add_argument("query", nargs="+")
    search.set_defaults(func=_cmd_search)

    doctor = sub.add_parser("doctor", parents=[sub_common], help="体检：死链与孤岛页面")
    doctor.add_argument("--entry", action="append", default=[], help="豁免的入口页（可重复）")
    doctor.set_defaults(func=_cmd_doctor)
    return parser


def _dump_json(payload) -> None:
    print(json.dumps(payload, ensure_ascii=False))


def _emit(as_json: bool, payload, lines) -> None:
    """统一渲染：JSON 单行，或逐行纯文本。"""
    if as_json:
        _dump_json(payload)
    else:
        for line in lines:
            print(line)


def _page_text(root: Path, rel_file: str) -> str:
    """渲染路径的原文读取；读不到（页面被删/索引过期）返回空串。"""
    try:
        return (root / rel_file).read_text(encoding="utf-8")
    except OSError:
        return ""


def _warn_if_stale(index, root: Path) -> None:
    if index_out_of_date(index, root):
        print("警告: 索引已过期，结果可能陈旧；请先运行 wiki-cli build", file=sys.stderr)


def _require_index(root: Path):
    index = load_index(root)  # IndexNotFound 由 main 统一兜底
    _warn_if_stale(index, root)
    return index


def _resolve_or_fail(index, page: str) -> str:
    resolved = index.resolve(page)
    if resolved is None:
        raise CommandError(f"页面不存在: {page}")
    return resolved


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (IndexNotFound, DuplicatePageError, CommandError) as exc:
        print(f"错误: {exc}", file=sys.stderr)
        return 1
