"""cli：argparse 接线 + 退出码，薄层。

退出码：0 正常；1 有发现（doctor 用）；2 用法错误。
对 vault 只读——这里没有任何写笔记的路径。
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import TypeVar

from . import index, render, resolve, search
from .index import VaultIndex
from .parse import Page

EXIT_OK = 0
EXIT_FINDINGS = 1
EXIT_USAGE = 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wiki-cli",
        description="个人本地 Markdown 知识库的结构洞察工具（对 vault 严格只读）",
    )
    parser.add_argument(
        "--vault",
        type=Path,
        default=None,
        help="vault 目录路径（默认当前工作目录）",
    )
    parser.add_argument(
        "--json",
        dest="as_json",
        action="store_true",
        help="输出 JSON 文档而非人读文本",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    links = subparsers.add_parser("links", help="列出页面的全部正向链接")
    links.add_argument("page", help="页面名（stem，或 子目录/页面 路径写法消歧）")
    backlinks = subparsers.add_parser("backlinks", help="列出引用某页面的全部反向引用")
    backlinks.add_argument("page", help="页面名（stem，或 子目录/页面 路径写法消歧）")
    tags = subparsers.add_parser("tags", help="全库标签聚合（无参）或查询标签下的页面")
    tags.add_argument("tag", nargs="?", default=None, help="标签名（# 前缀可选）")
    search = subparsers.add_parser("search", help="多关键词 AND 全文检索")
    search.add_argument(
        "keyword", nargs="+", help="关键词（大小写不敏感子串，多词 AND）"
    )
    subparsers.add_parser("doctor", help="全库体检：死链、孤岛页面与歧义链接")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    vault: Path = args.vault if args.vault is not None else Path.cwd()
    if not vault.exists():
        return _usage_error(parser, f"vault 不存在: {vault}")
    if not vault.is_dir():
        return _usage_error(parser, f"vault 不是目录: {vault}")
    if args.command == "search":
        if any(not kw.strip() for kw in args.keyword):
            return _usage_error(parser, "关键词不能为空")
        return _run_search(vault, args)
    vault_index = VaultIndex.from_vault(vault)
    if args.command == "links":
        return _run_links(vault_index, args)
    if args.command == "backlinks":
        return _run_backlinks(vault_index, args)
    if args.command == "tags":
        return _run_tags(vault_index, args)
    if args.command == "doctor":
        return _run_doctor(vault_index, args)
    parser.error(f"未知命令: {args.command}")
    return EXIT_USAGE  # pragma: no cover


def _usage_error(parser: argparse.ArgumentParser, message: str) -> int:
    """清晰用法提示 + exit 2（checklist 4）。"""
    parser.print_usage(sys.stderr)
    print(f"wiki-cli: 错误: {message}", file=sys.stderr)
    return EXIT_USAGE


_ResultT = TypeVar("_ResultT")


def _emit(
    args: argparse.Namespace,
    json_render: Callable[[_ResultT], str],
    human_render: Callable[[_ResultT], str],
    result: _ResultT,
) -> None:
    """输出模式分叉的唯一收口：`--json` 走 JSON 渲染，否则人读文本。

    同一结果对象喂给两个渲染函数（render 契约），行尾不另加换行。
    """
    print(json_render(result) if args.as_json else human_render(result), end="")


def _locate_page(vault_index: VaultIndex, name: str) -> Page | None:
    """三态定位查询目标页面，links 与 backlinks 完全同规（spec L19）：

    歧义 → stderr 列全部候选 + 提示路径写法消歧；大小写兜底可解析 → 正常
    返回页面；不存在（死链）→ 提示不存在。两种失败均由调用方 exit 2。
    """
    resolution = vault_index.resolve_link(name)
    if resolution.status == resolve.AMBIGUOUS:
        candidates = ", ".join(page.path for page in resolution.targets)
        print(
            f"页面名歧义: {name}（{candidates}）——用 子目录/页面 路径写法消歧",
            file=sys.stderr,
        )
        return None
    if resolution.status != resolve.RESOLVED:
        print(f"页面不存在: {name}", file=sys.stderr)
        return None
    return resolution.targets[0]


def _run_links(vault_index: VaultIndex, args: argparse.Namespace) -> int:
    page = _locate_page(vault_index, args.page)
    if page is None:
        return EXIT_USAGE
    entries = []
    for link in page.links:
        resolution = vault_index.resolve_link(link.target)
        target = (
            resolution.targets[0].path if resolution.status == resolve.RESOLVED else None
        )
        candidates = (
            tuple(page.path for page in resolution.targets)
            if resolution.status == resolve.AMBIGUOUS
            else ()
        )
        entries.append(
            render.LinkEntry(
                raw=link.raw,
                status=resolution.status,
                target=target,
                candidates=candidates,
            )
        )
    result = render.LinksResult(
        page_path=page.path, page_name=page.name, entries=tuple(entries)
    )
    _emit(args, render.links_json, render.links_human, result)
    return EXIT_OK


def _run_search(vault: Path, args: argparse.Namespace) -> int:
    result = search.search_vault(vault, args.keyword)
    _emit(args, render.search_json, render.search_human, result)
    return EXIT_OK


def _run_backlinks(vault_index: VaultIndex, args: argparse.Namespace) -> int:
    page = _locate_page(vault_index, args.page)
    if page is None:
        return EXIT_USAGE
    result = render.BacklinksResult(
        page_path=page.path,
        page_name=page.name,
        entries=vault_index.backlinks_for(page),
    )
    _emit(args, render.backlinks_json, render.backlinks_human, result)
    return EXIT_OK


def _run_tags(vault_index: VaultIndex, args: argparse.Namespace) -> int:
    name = (args.tag or "").removeprefix("#")  # `#` 前缀可选
    if name:
        result = render.TagPagesResult(
            tag=name, pages=tuple(page.path for page in vault_index.pages_for_tag(name))
        )
        _emit(args, render.tag_pages_json, render.tag_pages_human, result)
    else:
        counts = sorted(
            (
                render.TagCount(tag, len(pages))
                for tag, pages in vault_index.tag_pages().items()
            ),
            key=lambda c: (-c.page_count, c.tag),  # 页数降序、同数按字典序
        )
        result = render.TagsOverviewResult(tags=tuple(counts))
        _emit(args, render.tags_json, render.tags_human, result)
    return EXIT_OK


def _run_doctor(vault_index: VaultIndex, args: argparse.Namespace) -> int:
    findings = vault_index.doctor_findings()
    result = render.DoctorResult(
        page_count=len(vault_index.pages),
        link_count=sum(len(page.links) for page in vault_index.pages),
        tag_count=len(vault_index.tag_pages()),
        dead_links=findings.dead_links,
        orphans=findings.orphans,
        ambiguous=findings.ambiguous,
    )
    _emit(args, render.doctor_json, render.doctor_human, result)
    has_findings = bool(result.dead_links or result.orphans or result.ambiguous)
    return EXIT_FINDINGS if has_findings else EXIT_OK
