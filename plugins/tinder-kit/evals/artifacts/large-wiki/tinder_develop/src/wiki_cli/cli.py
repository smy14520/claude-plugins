"""CLI 编排与呈现层：子命令分发、全局 --json、退出码策略与中文输出。

退出码约定：0 = 正常 / 空结果；1 = doctor 发现问题；2 = 用法错误。
本层不含业务规则，只调用 Parser / LinkGraph 并格式化结果。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from wiki_cli import __version__
from wiki_cli.link_graph import LinkGraph, LinkEntry, PageRef

COMMANDS = ("links", "backlinks", "tags", "search", "doctor")

# 已交付的子命令处理函数（Vault, argparse.Namespace, 是否 JSON 输出）→ 退出码；
# 未列出的子命令以骨架形式运行。后续工单逐个填入。
_IMPLEMENTED: dict = {}


def _split_vault_prefix(argv: list[str]) -> tuple[str, list[str]]:
    """取出位于子命令之前的 Vault 目录位置参数（默认当前目录）。

    Vault 目录按对齐结论（Q1）是位置参数；为避免与各子命令自身的位置参数
    （如页面名、关键词）混淆，约定它必须写在子命令名之前：
    `wiki 目录 links 页面`。首个参数若不是子命令名、也不以 `-` 开头，即为 Vault。
    """
    if argv and argv[0] not in COMMANDS and not argv[0].startswith("-"):
        return argv[0], argv[1:]
    return ".", argv


def _add_json_flag(sub_parser: argparse.ArgumentParser) -> None:
    sub_parser.add_argument(
        "--json",
        action="store_true",
        default=argparse.SUPPRESS,
        help="以稳定英文 JSON 字段结构输出（供程序消费）",
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wiki",
        usage="wiki [Vault 目录] {links|backlinks|tags|search|doctor} [参数]",
        description="个人本地 Markdown Wiki 知识库命令行工具。",
    )
    parser.add_argument("--version", action="version", version=f"wiki {__version__}")
    parser.add_argument(
        "--json",
        action="store_true",
        default=argparse.SUPPRESS,
        help="以稳定英文 JSON 字段结构输出（供程序消费）",
    )

    subparsers = parser.add_subparsers(dest="command", required=True, metavar="子命令")

    p_links = subparsers.add_parser("links", help="列出 Link（指定页面，或全 Vault 汇总）")
    p_links.add_argument("page", nargs="?", help="页面名；省略时输出全 Vault 出链汇总")
    _add_json_flag(p_links)

    p_backlinks = subparsers.add_parser("backlinks", help="列出 Backlink（谁链接到我）")
    p_backlinks.add_argument("page", help="页面名")
    _add_json_flag(p_backlinks)

    p_tags = subparsers.add_parser("tags", help="聚合全 Vault Tag（计数 + 使用页面）")
    _add_json_flag(p_tags)

    p_search = subparsers.add_parser("search", help="Keyword Search（标题与正文关键词检索）")
    p_search.add_argument("keywords", nargs="+", help="关键词（空格分隔，取 AND）")
    _add_json_flag(p_search)

    subparsers.add_parser("doctor", help="Health Check（死链、孤岛页面与冲突体检）")
    p_doctor = subparsers.choices["doctor"]
    _add_json_flag(p_doctor)

    return parser


def _run_stub(command: str, json_output: bool) -> int:
    if json_output:
        print(json.dumps({"command": command, "implemented": False}, ensure_ascii=False))
    else:
        print(f"命令 {command} 尚未实现，将在后续工单交付。")
    return 0


def _link_dict(entry: LinkEntry) -> dict:
    """一条 Link 的 JSON 视图：稳定英文字段。"""
    return {
        "file": entry.source.rel_path,
        "line": entry.line,
        "target": entry.target,
        "resolved_page": entry.resolved.ref if entry.resolved else None,
    }


def _print_link_rows(entries: list[LinkEntry]) -> None:
    for entry in entries:
        destination = entry.resolved.ref if entry.resolved else entry.target
        print(f"  {entry.source.rel_path}:{entry.line} → {destination}")


def _run_links(vault: Path, ns, json_output: bool) -> int:
    graph = LinkGraph(vault)
    page_arg = getattr(ns, "page", None)

    if page_arg is not None:
        page = graph.find_page(page_arg)
        if page is None:
            print(f"错误：页面不存在：{page_arg}", file=sys.stderr)
            return 2
        entries = graph.links_of(page)
        if json_output:
            payload = {
                "command": "links",
                "vault": str(vault.resolve()),
                "page": page.name,
                "file": page.rel_path,
                "link_count": len(entries),
                "links": [_link_dict(entry) for entry in entries],
            }
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        elif not entries:
            print(f"页面 {page.name} 没有任何 Link。")
        else:
            print(f"页面 {page.name} 的 {len(entries)} 个 Link：")
            _print_link_rows(entries)
        return 0

    grouped = graph.pages_with_links()
    if json_output:
        payload = {
            "command": "links",
            "vault": str(vault.resolve()),
            "page_count": len(graph.pages),
            "link_count": len(graph.entries),
            "pages": [
                {
                    "page": page.name,
                    "file": page.rel_path,
                    "link_count": len(entries),
                    "links": [_link_dict(entry) for entry in entries],
                }
                for page, entries in grouped
            ],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    if not graph.pages:
        print("Vault 中没有 Page。")
        return 0
    if not grouped:
        print("Vault 中的 Page 均无 Link。")
        return 0
    print(f"Vault 出链汇总：{len(graph.pages)} 个 Page，共 {len(graph.entries)} 个 Link：")
    for page, entries in grouped:
        print(f"{page.ref}（{len(entries)} 个）：")
        _print_link_rows(entries)
    return 0


_IMPLEMENTED["links"] = _run_links


def _validate_vault(vault_str: str) -> tuple[Path | None, int]:
    vault = Path(vault_str)
    if not vault.exists():
        print(f"错误：Vault 路径不存在：{vault}", file=sys.stderr)
        return None, 2
    if not vault.is_dir():
        print(f"错误：Vault 路径不是目录：{vault}", file=sys.stderr)
        return None, 2
    return vault, 0


def _force_utf8_streams() -> None:
    """中文输出在非 UTF-8 控制台（如 Windows 默认代码页）下不崩。"""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8")
        except (OSError, ValueError):
            pass


def main(argv: list[str] | None = None) -> int:
    _force_utf8_streams()
    argv = list(sys.argv[1:]) if argv is None else list(argv)
    vault_str, argv = _split_vault_prefix(argv)

    parser = build_arg_parser()
    try:
        ns = parser.parse_args(argv)
    except SystemExit as exc:  # argparse 的用法错误 / --help / --version
        return int(exc.code) if isinstance(exc.code, int) else 0

    json_output = getattr(ns, "json", False)

    vault, code = _validate_vault(vault_str)
    if vault is None:
        return code

    handler = _IMPLEMENTED.get(ns.command)
    if handler is not None:
        return handler(vault, ns, json_output)
    return _run_stub(ns.command, json_output)
