"""命令行入口：命令面、人类/JSON 双输出、统一退出码。

退出码语义（收尾合同拍定）：
0 成功；1 业务性未命中（doctor 有缺陷、查询目标不存在、检索无命中）；
2 用法或 IO 错误。stderr 只出错误，stdout 只出结果，管道友好。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__, audit, indexer, query
from .model import INDEX_FILENAME, Page
from .parser import strip_md

EXIT_OK = 0
EXIT_MISS = 1
EXIT_ERROR = 2


def _common(suppress: bool) -> argparse.ArgumentParser:
    """全局参数组。子命令侧用 SUPPRESS 默认值，避免覆盖主解析器已解析的值。"""
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--root",
        type=Path,
        default=argparse.SUPPRESS if suppress else None,
        help="Vault 根目录，默认当前目录",
    )
    common.add_argument(
        "--json",
        action="store_true",
        default=argparse.SUPPRESS if suppress else False,
        help="输出机器可读 JSON",
    )
    return common


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wiki-cli",
        description="本地 Markdown 个人 Wiki 只读分析内核",
        parents=[_common(suppress=False)],
    )
    parser.add_argument(
        "--version", action="version", version=f"wiki-cli {__version__}"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser(
        "doctor", parents=[_common(suppress=True)], help="体检：死链/孤岛页/重名页/畸形 Frontmatter"
    )

    p = sub.add_parser("backlinks", parents=[_common(suppress=True)], help="反向引用查询")
    p.add_argument("page", help="页面名（可带 .md 后缀）")

    p = sub.add_parser("links", parents=[_common(suppress=True)], help="正向出链查询")
    p.add_argument("page", help="页面名（可带 .md 后缀）")

    p = sub.add_parser(
        "tags", parents=[_common(suppress=True)], help="标签聚合；带标签名则列出该标签下的页面"
    )
    p.add_argument("tag", nargs="?", default=None)

    p = sub.add_parser(
        "search", parents=[_common(suppress=True)], help="全文检索（多关键词 AND，子串匹配）"
    )
    p.add_argument("terms", nargs="+", metavar="词")

    sub.add_parser("build", parents=[_common(suppress=True)], help="强制重建并写出索引")
    return parser


def _load_index(root: Path) -> tuple[indexer.Index, bool]:
    return indexer.load(root)


def _page_or_fail(index, name: str) -> Page | None:
    """按身份取页面；不存在或重名歧义时向 stderr 报告，供调用方退出 1。"""
    pages = index.by_name().get(name, [])
    if not pages:
        print(f"页面不存在：{name}", file=sys.stderr)
        return None
    if len(pages) > 1:
        paths = ", ".join(sorted(p.rel_path for p in pages))
        print(f"页面名歧义（重名缺陷）：{name} → {paths}", file=sys.stderr)
        return None
    return pages[0]


def _emit_doctor(index, as_json: bool) -> int:
    report = audit.audit(index)
    if as_json:
        print(json.dumps(report.as_json(), ensure_ascii=False, indent=2))
        return EXIT_MISS if report.has_defects else EXIT_OK
    print(f"体检报告：Vault 共 {len(index.pages)} 页")
    if not report.has_defects:
        print("未发现缺陷。")
        return EXIT_OK
    if report.dead_links:
        print(f"\n死链 ({len(report.dead_links)}):")
        for d in report.dead_links:
            print(f"  - {d.path}:{d.line}  →  [[{d.raw}]]")
    if report.orphans:
        print(f"\n孤岛页 ({len(report.orphans)}):")
        for p in report.orphans:
            print(f"  - {p.rel_path}")
    if report.duplicates:
        print(f"\n重名页 ({len(report.duplicates)}):")
        for d in report.duplicates:
            print(f"  - {d.name}  →  {', '.join(d.paths)}")
    if report.malformed_frontmatter:
        print(f"\n畸形 Frontmatter ({len(report.malformed_frontmatter)}):")
        for p in report.malformed_frontmatter:
            print(f"  - {p.rel_path}")
    print(f"\n共 {report.defect_count} 处缺陷。")
    return EXIT_MISS


def _emit_backlinks(index, name: str, as_json: bool) -> int:
    if _page_or_fail(index, name) is None:
        return EXIT_MISS
    pairs = query.backlinks(index, name)
    if as_json:
        print(
            json.dumps(
                {
                    "page": name,
                    "backlinks": [
                        {
                            "page": p.name,
                            "path": p.rel_path,
                            "line": link.line,
                            "alias": link.alias,
                        }
                        for p, link in pairs
                    ],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return EXIT_OK
    print(f"「{name}」的入链 ({len(pairs)}):")
    for p, link in pairs:
        alias = f"|{link.alias}" if link.alias else ""
        print(f"  - {p.rel_path}:{link.line}  →  [[{link.target}{alias}]]")
    return EXIT_OK


def _emit_links(index, name: str, as_json: bool) -> int:
    page = _page_or_fail(index, name)
    if page is None:
        return EXIT_MISS
    links = query.outlinks(page)
    if as_json:
        print(
            json.dumps(
                {
                    "page": name,
                    "links": [
                        {
                            "raw": link.raw,
                            "target": link.target,
                            "line": link.line,
                            "status": query.resolve_target(index, link.target)[0],
                            "alias": link.alias,
                            "anchor": link.anchor,
                            "embed": link.embed,
                            "external": link.external,
                        }
                        for link in links
                    ],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return EXIT_OK
    print(f"「{name}」的出链 ({len(links)}):")
    for link in links:
        if link.external:
            status = "外部"
        else:
            resolved = query.resolve_target(index, link.target)[0]
            status = {
                query.LinkStatus.RESOLVED: "已解析",
                query.LinkStatus.DEAD: "死链",
                query.LinkStatus.AMBIGUOUS: "歧义",
            }[resolved]
        print(f"  - L{link.line}  [[{link.raw}]]  [{status}]")
    return EXIT_OK


def _emit_tags(index, tag: str | None, as_json: bool) -> int:
    if tag is None:
        counts = query.tag_counts(index)
        if as_json:
            print(
                json.dumps(
                    {"tags": [{"tag": t, "page_count": c} for t, c in counts]},
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return EXIT_OK
        print(f"标签 ({len(counts)}):")
        for t, c in counts:
            print(f"  {t} ×{c}")
        return EXIT_OK
    pages = query.tag_pages(index, tag)
    if not pages:
        print(f"标签不存在或无页面：{tag}", file=sys.stderr)
        return EXIT_MISS
    if as_json:
        print(
            json.dumps(
                {
                    "tag": tag,
                    "pages": [{"name": p.name, "path": p.rel_path} for p in pages],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return EXIT_OK
    print(f"标签「{tag}」下的页面 ({len(pages)}):")
    for p in pages:
        print(f"  - {p.rel_path}")
    return EXIT_OK


def _emit_search(index, root: Path, terms: list[str], as_json: bool) -> int:
    hits = query.search(index, root, terms)
    if as_json:
        print(
            json.dumps(
                {
                    "query": terms,
                    "hits": [
                        {
                            "name": h.page.name,
                            "path": h.page.rel_path,
                            "identity_hit": h.identity_hit,
                            "count": h.count,
                            "snippet": h.snippet,
                        }
                        for h in hits
                    ],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return EXIT_OK if hits else EXIT_MISS
    if not hits:
        print("无命中。", file=sys.stderr)
        return EXIT_MISS
    print(f"命中 {len(hits)} 页:")
    for h in hits:
        flag = " [身份命中]" if h.identity_hit else ""
        print(f"  - {h.page.name} ({h.page.rel_path})  命中 {h.count} 处{flag}")
        if h.snippet:
            print(f"      {h.snippet}")
    return EXIT_OK


def _emit_build(root: Path, as_json: bool) -> int:
    index = indexer.rebuild(root)
    link_count = sum(len(p.links) for p in index.pages)
    tag_count = len(index.by_tag())
    cache = root / INDEX_FILENAME
    if as_json:
        print(
            json.dumps(
                {
                    "pages": len(index.pages),
                    "links": link_count,
                    "tags": tag_count,
                    "cache": str(cache),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return EXIT_OK
    print(
        f"索引已重建：{len(index.pages)} 页 / {link_count} 条链接 / "
        f"{tag_count} 个标签 → {cache}"
    )
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    root = (args.root or Path.cwd()).resolve()
    if not root.is_dir():
        print(f"Vault 根目录不存在：{root}", file=sys.stderr)
        return EXIT_ERROR
    try:
        if args.command == "build":
            return _emit_build(root, args.json)
        index, _ = _load_index(root)
    except OSError as exc:
        print(f"IO 错误：{exc}", file=sys.stderr)
        return EXIT_ERROR

    if args.command == "doctor":
        return _emit_doctor(index, args.json)
    if args.command == "backlinks":
        return _emit_backlinks(index, strip_md(args.page), args.json)
    if args.command == "links":
        return _emit_links(index, strip_md(args.page), args.json)
    if args.command == "tags":
        return _emit_tags(index, args.tag, args.json)
    if args.command == "search":
        return _emit_search(index, root, args.terms, args.json)
    parser.error(f"未知命令：{args.command}")
    return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
