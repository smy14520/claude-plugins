"""wiki 命令行入口：纯标准库 argparse 薄壳（ADR-0002）。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .doctor import diagnose
from .indexer import build_index, write_index
from .model import Page, WikiIndex
from .search import search


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    root = (
        Path(args.root).expanduser().resolve() if args.root else Path.cwd().resolve()
    )
    if not root.is_dir():
        print(f"错误：知识库根目录不存在：{root}", file=sys.stderr)
        return 2
    index = build_index(root)  # 每条命令全量重建（ADR-0001）
    return args.func(args, index)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wiki", description="本地 Markdown 个人 Wiki 知识库管理内核"
    )
    parser.add_argument("--root", default=None, help="知识库根目录（默认：当前目录）")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("build", help="全量重建索引并落盘 .wiki_index.json")
    p.add_argument("--json", action="store_true", help="以 JSON 输出")
    p.set_defaults(func=_cmd_build)

    p = sub.add_parser("backlinks", help="查询页面的反向引用")
    p.add_argument("page")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=_cmd_backlinks)

    p = sub.add_parser("links", help="查询页面的出链（死链显式标注）")
    p.add_argument("page")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=_cmd_links)

    p = sub.add_parser("tags", help="标签聚合；带参时列出该标签下页面")
    p.add_argument("tag", nargs="?", default=None)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=_cmd_tags)

    p = sub.add_parser("search", help="全文检索（AND 子串，命中次数排序）")
    p.add_argument("terms", nargs="+")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=_cmd_search)

    p = sub.add_parser("doctor", help="体检：死链 / 孤岛页面 / 重复标题")
    p.add_argument("--strict", action="store_true", help="孤岛页面也判为失败")
    p.add_argument(
        "--ignore", action="append", default=[], metavar="PAGE", help="豁免页面（可多次）"
    )
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=_cmd_doctor)
    return parser


def _find_page(index: WikiIndex, name: str) -> Page | None:
    group = index.title_map().get(name)
    return group[0] if group else None


def _stats(index: WikiIndex) -> tuple[int, int, int]:
    pages = len(index.pages)
    links = sum(len(p.links) for p in index.pages)
    tags = len({t for p in index.pages for t in p.tags})
    return pages, links, tags


def _cmd_build(args, index: WikiIndex) -> int:
    target = write_index(index)
    pages, links, tags = _stats(index)
    if args.json:
        print(
            json.dumps(
                {
                    "index_file": target.name,
                    "pages": pages,
                    "links": links,
                    "tags": tags,
                },
                ensure_ascii=False,
                sort_keys=True,
                indent=2,
            )
        )
    else:
        print(f"索引已写入 {target.name} · 页面 {pages} · 链接 {links} · 标签 {tags}")
    return 0


def _cmd_backlinks(args, index: WikiIndex) -> int:
    if _find_page(index, args.page) is None:
        print(f"错误：页面不存在：{args.page}", file=sys.stderr)
        return 1
    sources = [
        {"title": p.title, "path": p.path}
        for p in index.pages
        if args.page in p.links and p.title != args.page
    ]
    if args.json:
        print(
            json.dumps(
                {"page": args.page, "sources": sources},
                ensure_ascii=False,
                sort_keys=True,
                indent=2,
            )
        )
    else:
        print(f"反向引用 · 页面「{args.page}」（{len(sources)}）：")
        for s in sources:
            print(f"  - {s['title']}（{s['path']}）")
    return 0


def _cmd_links(args, index: WikiIndex) -> int:
    page = _find_page(index, args.page)
    if page is None:
        print(f"错误：页面不存在：{args.page}", file=sys.stderr)
        return 1
    title_map = index.title_map()
    targets = [{"target": t, "resolved": t in title_map} for t in page.links]
    if args.json:
        print(
            json.dumps(
                {"page": args.page, "links": targets},
                ensure_ascii=False,
                sort_keys=True,
                indent=2,
            )
        )
    else:
        print(f"出链 · 页面「{args.page}」（{len(targets)}）：")
        for t in targets:
            mark = "" if t["resolved"] else "（死链）"
            print(f"  - {t['target']}{mark}")
    return 0


def _cmd_tags(args, index: WikiIndex) -> int:
    if args.tag is None:
        counts: dict[str, int] = {}
        for p in index.pages:
            for t in p.tags:
                counts[t] = counts.get(t, 0) + 1
        items = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
        if args.json:
            print(
                json.dumps(
                    {"tags": [{"tag": t, "pages": n} for t, n in items]},
                    ensure_ascii=False,
                    sort_keys=True,
                    indent=2,
                )
            )
        else:
            print(f"标签聚合（{len(items)}）：")
            for t, n in items:
                print(f"  - #{t}（{n} 页）")
        return 0
    tag = args.tag.lower().lstrip("#")
    pages = [{"title": p.title, "path": p.path} for p in index.pages if tag in p.tags]
    if args.json:
        print(
            json.dumps(
                {"tag": tag, "pages": pages},
                ensure_ascii=False,
                sort_keys=True,
                indent=2,
            )
        )
    else:
        print(f"标签 #{tag}（{len(pages)} 页）：")
        for item in pages:
            print(f"  - {item['title']}（{item['path']}）")
    return 0


def _cmd_search(args, index: WikiIndex) -> int:
    hits = search(index, args.terms)
    if args.json:
        print(
            json.dumps(
                {
                    "terms": args.terms,
                    "hits": [
                        {
                            "title": h.page.title,
                            "path": h.page.path,
                            "count": h.count,
                            "snippet": h.snippet,
                        }
                        for h in hits
                    ],
                },
                ensure_ascii=False,
                sort_keys=True,
                indent=2,
            )
        )
    else:
        print(f"检索 {' '.join(args.terms)} · 命中 {len(hits)} 页：")
        for h in hits:
            print(f"  - {h.page.title}（{h.page.path}）· 命中 {h.count} 次")
            print(f"      {h.snippet}")
    return 0


def _cmd_doctor(args, index: WikiIndex) -> int:
    report = diagnose(index, ignore=set(args.ignore))
    duplicates = [
        {"title": title, "paths": [p.path for p in index.title_map()[title]]}
        for title in report.duplicates
    ]
    if args.json:
        print(
            json.dumps(
                {
                    "dead_links": [
                        {"source": s, "target": t} for s, t in report.dead_links
                    ],
                    "orphans": report.orphans,
                    "duplicates": duplicates,
                },
                ensure_ascii=False,
                sort_keys=True,
                indent=2,
            )
        )
    else:
        pages, links, _ = _stats(index)
        print(f"体检报告 · 页面 {pages} · 链接 {links}")
        print(f"死链（{len(report.dead_links)}）：")
        for s, t in report.dead_links:
            print(f"  - {s} → {t}")
        print(f"孤岛页面（{len(report.orphans)}）：")
        for title in report.orphans:
            print(f"  - {title}")
        print(f"重复标题（{len(duplicates)}）：")
        for d in duplicates:
            print(f"  - {d['title']}: {', '.join(d['paths'])}")
    failed = report.blocking or (args.strict and bool(report.orphans))
    return 1 if failed else 0
