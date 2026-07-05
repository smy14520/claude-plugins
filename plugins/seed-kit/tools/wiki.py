#!/usr/bin/env python3
"""seed wiki — 项目本地 `.wiki/` 导航层 CLI。

独立工具：零依赖 arbor / `.arbor` 状态。wiki 是导航层，永不是 source of truth；
本 CLI 只做 markdown 页面的索引、搜索、收集与体检。

页面模型（两个正交轴）：
- `type`  —— 结构轴，封闭集（工具如何消费该页面）。
- `area`  —— 领域轴，自由形式（属于**本**项目的哪一部分，如渲染管线 / 权限 /
  资产管线）。分类随项目而变；wiki skill 从项目 profile 派生 area，CLI 永不校验。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
TOKEN_RE = re.compile(r"[\w]+", re.IGNORECASE)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
SYMBOL_RE = re.compile(r"`([A-Za-z_][A-Za-z0-9_:.#/-]*)`")
REQUIRED_FRONTMATTER = {"title", "description", "type"}
VALID_PAGE_TYPES = {"entity", "concept", "gotcha", "decision", "source", "module", "cross_cut"}
# 符号锚：`lib/core/Axios.js#_request` — 存符号不存行号，显示时 resolve
CODE_ANCHOR_RE = re.compile(r"`?([\w./-]+\.\w+)#([\w.#-]+)`?")
# 旧式行号引用（lint 降级警告用）
LINE_LOCATOR_RE = re.compile(r"(?:^|[\s`])(?:[\w./-]+\.(?:py|ts|tsx|js|jsx|go|rs|java|rb|php|css|scss|md|json|yaml|yml)):(?:L)?\d+|\bline\s+\d+\b", re.IGNORECASE)


class WikiError(Exception):
    pass


def wiki_root_path(root: Path, wiki_root: str | None = None) -> Path:
    value = wiki_root.strip() if isinstance(wiki_root, str) and wiki_root.strip() else ".arbor/.wiki"
    path = Path(value)
    if path.is_absolute():
        return path
    return root / path


def _parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text
    raw = text[4:end].strip().splitlines()
    body = text[end + 4 :].lstrip("\n")
    meta: dict[str, Any] = {}
    for line in raw:
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            items = [item.strip().strip('"\'') for item in value[1:-1].split(",") if item.strip()]
            meta[key] = items
        else:
            meta[key] = value.strip('"\'')
    return meta, body


def _first_paragraph(body: str) -> str:
    lines: list[str] = []
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped:
            if lines:
                break
            continue
        if stripped.startswith("#"):
            continue
        lines.append(stripped)
    return " ".join(lines)


def _page_title(path: Path, meta: dict[str, Any], body: str) -> str:
    title = meta.get("title")
    if isinstance(title, str) and title.strip():
        return title.strip()
    for line in body.splitlines():
        match = HEADING_RE.match(line)
        if match:
            return match.group(2).strip()
    return path.stem


def _tags(meta: dict[str, Any]) -> list[str]:
    tags = meta.get("tags")
    if isinstance(tags, list):
        return [item for item in tags if isinstance(item, str) and item]
    if isinstance(tags, str):
        return [item.strip() for item in tags.split(",") if item.strip()]
    return []


def _links(body: str) -> list[str]:
    result: list[str] = []
    for match in WIKILINK_RE.finditer(body):
        target = match.group(1).strip()
        if target and target not in result:
            result.append(target)
    return result


def _locators(body: str) -> list[dict[str, str]]:
    locators: list[dict[str, str]] = []
    for line in body.splitlines():
        heading = HEADING_RE.match(line)
        if heading:
            level = len(heading.group(1))
            title = heading.group(2).strip()
            locators.append({"kind": "heading", "level": str(level), "name": title})
        for symbol in SYMBOL_RE.findall(line):
            locators.append({"kind": "symbol", "name": symbol})
    seen: set[tuple[str, str]] = set()
    unique: list[dict[str, str]] = []
    for item in locators:
        key = (item.get("kind", ""), item.get("name", ""))
        if key not in seen:
            seen.add(key)
            unique.append(item)
    return unique


def _extract_anchors(body: str) -> list[dict[str, str]]:
    """从页面正文提取 `path#Symbol` 格式的代码锚点。"""
    anchors: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for match in CODE_ANCHOR_RE.finditer(body):
        file_ref = match.group(1).strip()
        symbol = match.group(2).strip()
        # 过滤明显的非文件路径（如 wikilink 内部锚点 [[page#heading]]）
        if not re.search(r"\.\w+$", file_ref):
            continue
        key = (file_ref, symbol)
        if key not in seen:
            seen.add(key)
            anchors.append({"file": file_ref, "symbol": symbol})
    return anchors


def _resolve_anchor(root: Path, file_ref: str, symbol: str) -> dict[str, Any]:
    """在文件里 grep symbol，返回当前行号列表。行号不落盘——每次调用实时计算。"""
    target = root / file_ref
    if not target.exists():
        return {"file": file_ref, "symbol": symbol, "found": False, "lines": [], "resolved": f"{file_ref}#{symbol} (文件不存在)"}
    try:
        text = target.read_text(encoding="utf-8")
        lines = [i for i, line in enumerate(text.splitlines(), start=1) if symbol in line]
        resolved = f"{file_ref}:{lines[0]}" if lines else f"{file_ref}#{symbol} (symbol 未找到)"
        return {"file": file_ref, "symbol": symbol, "found": len(lines) > 0, "lines": lines, "resolved": resolved}
    except Exception:
        return {"file": file_ref, "symbol": symbol, "found": False, "lines": [], "resolved": f"{file_ref}#{symbol} (读取失败)"}


def _page_entry(root: Path, path: Path, include_content: bool) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    meta, body = _parse_frontmatter(text)
    rel = path.relative_to(root).as_posix()
    summary = meta.get("summary") if isinstance(meta.get("summary"), str) else _first_paragraph(body)
    entry: dict[str, Any] = {
        "path": rel,
        "title": _page_title(path, meta, body),
        "description": meta.get("description") if isinstance(meta.get("description"), str) else "",
        "summary": summary,
        "tags": _tags(meta),
        "type": meta.get("type") if isinstance(meta.get("type"), str) else None,
        "area": meta.get("area") if isinstance(meta.get("area"), str) else None,
        "package": meta.get("package") if isinstance(meta.get("package"), str) else None,
        "source_checkpoint": meta.get("source_checkpoint") if isinstance(meta.get("source_checkpoint"), str) else None,
        "links": _links(body),
        "backlinks": [],
        "locators": _locators(body),
        "anchors": _extract_anchors(body),
    }
    if include_content:
        entry["content"] = body
    return entry


def _resolve_wikilink(link: str, by_title: dict[str, dict[str, Any]], by_stem: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    return by_title.get(link) or by_stem.get(Path(link).stem)


def _write_index_md(directory: Path, pages: list[dict[str, Any]], root: Path | None = None) -> None:
    """生成 .wiki/index.md（按 type 分组）并追加 .wiki/log.md。"""
    grouped: dict[str, list[dict[str, Any]]] = {}
    for page in pages:
        t = page.get("type") or "unknown"
        grouped.setdefault(t, []).append(page)

    lines = ["---", "title: Wiki Index", "description: 项目知识导航——按类型分组的 wiki 页面索引", "type: index", "---", "", "# Wiki Index", ""]
    for t in sorted(grouped.keys()):
        lines.append(f"## {t}")
        lines.append("")
        for p in grouped[t]:
            # 用相对于 wiki 根目录的路径，例如 gotcha/interceptor-ordering.md
            page_path = Path(p["path"])
            stem = page_path.name
            # page_path 是相对于项目根的路径，需要转成相对于 wiki 根的路径
            if root and page_path.is_absolute():
                try:
                    rel = str(page_path.relative_to(directory))
                except ValueError:
                    rel = stem
            else:
                # page_path 是相对路径（相对于 root），拼接后转相对
                abs_page = (root / page_path).resolve() if root else page_path
                abs_wiki = directory.resolve()
                try:
                    rel = str(abs_page.relative_to(abs_wiki))
                except ValueError:
                    rel = stem
            desc = p.get("description", "")
            lines.append(f"- [{p['title']}]({rel}) — {desc}")
        lines.append("")
    (directory / "index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # 维护 log.md：记录本次索引的页面快照
    _append_log_md(directory, pages)


def _append_log_md(directory: Path, pages: list[dict[str, Any]]) -> None:
    """追加 .wiki/log.md 条目，记录当前页面快照和变更。"""
    from datetime import datetime, timezone
    log_path = directory / "log.md"
    old_stems: set[str] = set()
    old_lines: list[str] = []
    if log_path.exists():
        old_text = log_path.read_text(encoding="utf-8")
        old_lines = old_text.splitlines()
        # 从上一次快照中提取页面列表
        for line in old_lines:
            if line.startswith("- [") and "](" in line:
                stem = line.split("](")[1].split(")")[0] if "](" in line else ""
                if stem:
                    old_stems.add(stem)

    new_stems = {Path(p["path"]).name for p in pages}
    added = new_stems - old_stems
    removed = old_stems - new_stems

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    entry = [f"## [{now}] snapshot | {len(pages)} pages"]
    if added:
        entry.append(f"+ {len(added)} added: {', '.join(sorted(added))}")
    if removed:
        entry.append(f"- {len(removed)} removed: {', '.join(sorted(removed))}")
    if not added and not removed:
        entry.append("no changes")
    entry.append("")

    # 保留旧内容，在前面插入新条目
    new_content = "\n".join(entry) + "\n" + ("\n".join(old_lines) if old_lines else "")
    log_path.write_text(new_content, encoding="utf-8")


def wiki_index(root: Path, wiki_root: str | None = None, tag: str | None = None, include_content: bool = False, resolve: bool = False) -> dict[str, Any]:
    directory = wiki_root_path(root, wiki_root)
    if not directory.exists():
        return {"wiki_root": str(directory.relative_to(root)) if directory.is_relative_to(root) else str(directory), "pages": []}
    pages = [_page_entry(root, path, include_content) for path in sorted(directory.rglob("*.md")) if path.is_file() and path.name not in ("index.md", "log.md")]
    by_title = {page["title"]: page for page in pages}
    by_stem = {Path(page["path"]).stem: page for page in pages}
    for page in pages:
        for link in page["links"]:
            target = _resolve_wikilink(link, by_title, by_stem)
            if target is not None and page["title"] not in target["backlinks"]:
                target["backlinks"].append(page["title"])
    if tag:
        pages = [page for page in pages if tag in page.get("tags", [])]
    # --resolve: 实时解析符号锚到当前行号
    if resolve:
        for page in pages:
            resolved = []
            for anchor in page.get("anchors", []):
                resolved.append(_resolve_anchor(root, anchor["file"], anchor["symbol"]))
            page["resolved_anchors"] = resolved
    wiki_root_value = directory.relative_to(root).as_posix() if directory.is_relative_to(root) else str(directory)
    return {"wiki_root": wiki_root_value, "pages": pages}


def _tokens(value: Any) -> set[str]:
    if isinstance(value, list):
        return set().union(*(_tokens(item) for item in value)) if value else set()
    if not isinstance(value, str):
        return set()
    return {item.casefold() for item in TOKEN_RE.findall(value)}


def _lint_issue(code: str, path: str, message: str, **extra: Any) -> dict[str, Any]:
    issue = {"code": code, "path": path, "message": message}
    issue.update(extra)
    return issue


def _hidden_path_parts(relative_path: str) -> list[str]:
    return [part for part in Path(relative_path).parts if part.startswith(".") and part not in (".wiki", ".arbor")]


def wiki_lint(root: Path, wiki_root: str | None = None) -> dict[str, Any]:
    directory = wiki_root_path(root, wiki_root)
    wiki_root_value = directory.relative_to(root).as_posix() if directory.is_relative_to(root) else str(directory)
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    if not directory.exists():
        return {"ok": True, "wiki_root": wiki_root_value, "errors": [], "warnings": [], "summary": {"error_count": 0, "warning_count": 0}}

    pages: list[dict[str, Any]] = []
    by_title: dict[str, list[dict[str, Any]]] = {}
    by_stem: dict[str, list[dict[str, Any]]] = {}
    module_packages: dict[str, list[dict[str, Any]]] = {}
    for path in sorted(directory.rglob("*.md")):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        meta, body = _parse_frontmatter(text)
        rel = path.relative_to(root).as_posix() if path.is_relative_to(root) else str(path)
        title = _page_title(path, meta, body)
        page = {"path": rel, "meta": meta, "body": body, "title": title, "stem": path.stem, "links": _links(body), "type": meta.get("type")}
        pages.append(page)
        by_title.setdefault(title, []).append(page)
        by_stem.setdefault(path.stem, []).append(page)
        missing = [field for field in sorted(REQUIRED_FRONTMATTER) if not isinstance(meta.get(field), str) or not str(meta.get(field)).strip()]
        if missing:
            errors.append(_lint_issue("missing_frontmatter", rel, "缺少必需的 frontmatter：" + ", ".join(missing), fields=missing))
        page_type = meta.get("type")
        if isinstance(page_type, str) and page_type not in VALID_PAGE_TYPES:
            errors.append(_lint_issue("invalid_type", rel, f"无效的 frontmatter type：{page_type}", type=page_type))
        if not meta.get("summary"):
            warnings.append(_lint_issue("missing_summary", rel, "缺少 frontmatter summary"))
        if not _tags(meta):
            warnings.append(_lint_issue("missing_tags", rel, "缺少 frontmatter tags"))
        hidden_parts = _hidden_path_parts(rel)
        if hidden_parts:
            warnings.append(_lint_issue("hidden_path", rel, "wiki 页面位于隐藏路径下：" + ", ".join(hidden_parts), parts=hidden_parts))
        if page_type == "module":
            package = meta.get("package")
            if isinstance(package, str) and package.strip():
                module_packages.setdefault(package.strip(), []).append(page)
            else:
                warnings.append(_lint_issue("module_missing_package", rel, "module 类型页面缺少 package frontmatter"))
            if not isinstance(meta.get("source_checkpoint"), str) or not str(meta.get("source_checkpoint")).strip():
                warnings.append(_lint_issue("module_missing_source_checkpoint", rel, "module 类型页面缺少 source_checkpoint frontmatter"))
        # 旧式行号引用：降级警告（建议迁移到符号锚）
        for line_number, line in enumerate(body.splitlines(), start=1):
            if LINE_LOCATOR_RE.search(line):
                warnings.append(_lint_issue("legacy_line_locator", rel, "使用了旧式行号引用（`file:行号`），建议迁移为符号锚（`file#Symbol`）", line=line_number))
                break
        # 符号锚校验：文件是否存在、符号是否可找到
        anchors = _extract_anchors(body)
        for anchor in anchors:
            result = _resolve_anchor(root, anchor["file"], anchor["symbol"])
            if not result["found"]:
                if "文件不存在" in result.get("resolved", ""):
                    errors.append(_lint_issue("stale_anchor", rel, f"代码锚点指向的文件不存在：{anchor['file']}", file=anchor["file"]))
                else:
                    warnings.append(_lint_issue("stale_anchor", rel, f"符号锚未找到符号：{anchor['file']}#{anchor['symbol']}——代码可能已变更", file=anchor["file"], symbol=anchor["symbol"]))

    single_by_title = {title: items[0] for title, items in by_title.items() if len(items) == 1}
    single_by_stem = {stem: items[0] for stem, items in by_stem.items() if len(items) == 1}
    for title, items in sorted(by_title.items()):
        if len(items) > 1:
            errors.append(_lint_issue("duplicate_title", items[0]["path"], f"wiki 标题重复：{title}", title=title, paths=[item["path"] for item in items]))
    for stem, items in sorted(by_stem.items()):
        if len(items) > 1 and stem != "index":
            errors.append(_lint_issue("duplicate_stem", items[0]["path"], f"wiki 文件 stem 重复：{stem}", stem=stem, paths=[item["path"] for item in items]))
    for package, items in sorted(module_packages.items()):
        if len(items) > 1:
            errors.append(_lint_issue("duplicate_module_package", items[0]["path"], f"module package 重复：{package}", package=package, paths=[item["path"] for item in items]))
    for page in pages:
        for link in page["links"]:
            if _resolve_wikilink(link, single_by_title, single_by_stem) is None:
                errors.append(_lint_issue("broken_wikilink", page["path"], f"失效的 wikilink：{link}", target=link))

    linked_paths: set[str] = set()
    for page in pages:
        for link in page["links"]:
            target = _resolve_wikilink(link, single_by_title, single_by_stem)
            if target is not None:
                linked_paths.add(target["path"])
    for page in pages:
        if page["path"] not in linked_paths and page["links"] == [] and Path(page["path"]).name != "index.md":
            warnings.append(_lint_issue("orphan_page", page["path"], "页面没有 wikilink 也没有 backlink"))

    return {
        "ok": not errors,
        "wiki_root": wiki_root_value,
        "errors": errors,
        "warnings": warnings,
        "summary": {"error_count": len(errors), "warning_count": len(warnings)},
    }


def wiki_search(root: Path, query: str, wiki_root: str | None = None, limit: int | None = None) -> dict[str, Any]:
    query_tokens = _tokens(query)
    if not query_tokens:
        raise WikiError("wiki 搜索 query 至少要含一个 token")
    indexed = wiki_index(root, wiki_root, include_content=True)
    results: list[dict[str, Any]] = []
    weights = {
        "type": 20,
        "title": 8,
        "tags": 6,
        "area": 6,
        "description": 5,
        "summary": 4,
        "path": 2,
        "locators": 2,
        "content": 1,
    }
    for page in indexed["pages"]:
        score = 0
        matched_fields: list[str] = []
        locator_text = " ".join(item.get("name", "") for item in page.get("locators", []) if isinstance(item, dict))
        fields = {
            "title": page.get("title"),
            "type": page.get("type"),
            "tags": page.get("tags"),
            "area": page.get("area"),
            "description": page.get("description"),
            "summary": page.get("summary"),
            "path": page.get("path"),
            "locators": locator_text,
            "content": page.get("content"),
        }
        for field, value in fields.items():
            matches = query_tokens.intersection(_tokens(value))
            if matches:
                matched_fields.append(field)
                score += len(matches) * weights[field]
        if score:
            page_result = {key: value for key, value in page.items() if key != "content"}
            page_result["score"] = score
            page_result["matched_fields"] = matched_fields
            page_result["reason"] = "命中：" + ", ".join(matched_fields)
            results.append(page_result)
    results.sort(key=lambda item: (-item["score"], item["path"]))
    if limit is not None:
        results = results[:limit]
    return {"wiki_root": indexed["wiki_root"], "query": query, "results": results}


def wiki_collect(root: Path, query: str, wiki_root: str | None = None, limit: int = 5) -> dict[str, Any]:
    search = wiki_search(root, query, wiki_root, limit)
    selected = []
    for item in search["results"]:
        selected.append(
            {
                "path": item["path"],
                "title": item["title"],
                "description": item.get("description"),
                "summary": item.get("summary"),
                "type": item.get("type"),
                "area": item.get("area"),
                "tags": item.get("tags", []),
                "links": item.get("links", []),
                "backlinks": item.get("backlinks", []),
                "locators": item.get("locators", []),
                "score": item.get("score"),
                "reason": item.get("reason"),
            }
        )
    return {"wiki_root": search["wiki_root"], "query": query, "selected": selected}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="seed wiki", description="项目本地 .wiki 导航层：index / search / collect / lint")
    parser.add_argument("--root", default=".", help="项目根目录（含 .wiki/）")
    sub = parser.add_subparsers(dest="command", required=True)

    index_parser = sub.add_parser("index", help="为 wiki 页面建立索引")
    index_parser.add_argument("--wiki-root", default=".arbor/.wiki")
    index_parser.add_argument("--tag")
    index_parser.add_argument("--include-content", choices=["true", "false"], default="false")
    index_parser.add_argument("--resolve", action="store_true", dest="resolve_anchors", help="实时解析符号锚为当前行号")
    index_parser.add_argument("--json", dest="json_output", action="store_true", help="输出 JSON 格式")
    index_parser.add_argument("--write", action="store_true", dest="write_index", help="生成索引文件 index.md 和日志 log.md")

    search_parser = sub.add_parser("search", help="按 token 评分搜索 wiki 页面")
    search_parser.add_argument("query")
    search_parser.add_argument("--wiki-root", default=".arbor/.wiki")
    search_parser.add_argument("--limit", type=int)
    search_parser.add_argument("--json", dest="json_output", action="store_true", help="输出 JSON 格式")

    collect_parser = sub.add_parser("collect", help="收集相关 wiki 页面的精简摘要")
    collect_parser.add_argument("--query", required=True)
    collect_parser.add_argument("--wiki-root", default=".arbor/.wiki")
    collect_parser.add_argument("--limit", type=int, default=5)
    collect_parser.add_argument("--json", dest="json_output", action="store_true", help="输出 JSON 格式")

    lint_parser = sub.add_parser("lint", help="体检 wiki 页面（不修改）")
    lint_parser.add_argument("--wiki-root", default=".arbor/.wiki")
    lint_parser.add_argument("--json", dest="json_output", action="store_true", help="输出 JSON 格式")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    json_output = getattr(args, "json_output", False)
    try:
        if args.command == "index":
            result = wiki_index(root, args.wiki_root, args.tag, args.include_content == "true", resolve=getattr(args, "resolve_anchors", False))
            if json_output:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                for page in result["pages"]:
                    print(f"{page['path']} [{page.get('type') or '-'}] {page['title']}")
            if getattr(args, "write_index", False):
                directory = wiki_root_path(root, args.wiki_root)
                _write_index_md(directory, result["pages"], root)
                print(f"已生成 {directory.relative_to(root).as_posix() if directory.is_relative_to(root) else str(directory)}/index.md（{len(result['pages'])} pages）")
            return 0
        if args.command == "search":
            result = wiki_search(root, args.query, args.wiki_root, args.limit)
            if json_output:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                for item in result["results"]:
                    print(f"{item['score']:>4} {item['path']} — {item['reason']}")
            return 0
        if args.command == "collect":
            result = wiki_collect(root, args.query, args.wiki_root, args.limit)
            if json_output:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                for item in result["selected"]:
                    print(f"{item['path']} [{item.get('type') or '-'}] {item['title']}")
            return 0
        if args.command == "lint":
            result = wiki_lint(root, args.wiki_root)
            print(json.dumps(result, ensure_ascii=False, indent=2) if json_output else f"ok={result['ok']} errors={result['summary']['error_count']} warnings={result['summary']['warning_count']}")
            return 0 if result["ok"] else 1
    except WikiError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
