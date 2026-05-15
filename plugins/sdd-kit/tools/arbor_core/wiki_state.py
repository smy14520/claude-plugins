from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .errors import ArborError
from .fs import *
from .prd_slices import parse_prd_slices
from .state import ensure_execution
from .validation import validate_package

WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
TOKEN_RE = re.compile(r"[\w]+", re.IGNORECASE)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
SYMBOL_RE = re.compile(r"`([A-Za-z_][A-Za-z0-9_:.#/-]*)`")
REQUIRED_FRONTMATTER = {"title", "description", "type"}
VALID_PAGE_TYPES = {"entity", "concept", "gotcha", "decision", "source", "module", "cross_cut"}
LINE_LOCATOR_RE = re.compile(r"(?:^|[\s`])(?:[\w./-]+\.(?:py|ts|tsx|js|jsx|go|rs|java|rb|php|css|scss|md|json|yaml|yml)):(?:L)?\d+|\bline\s+\d+\b", re.IGNORECASE)




def wiki_root_path(root: Path, wiki_root: str | None = None) -> Path:
    value = wiki_root.strip() if isinstance(wiki_root, str) and wiki_root.strip() else ".wiki"
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
        "package": meta.get("package") if isinstance(meta.get("package"), str) else None,
        "source_checkpoint": meta.get("source_checkpoint") if isinstance(meta.get("source_checkpoint"), str) else None,
        "links": _links(body),
        "backlinks": [],
        "locators": _locators(body),
    }
    if include_content:
        entry["content"] = body
    return entry


def _resolve_wikilink(link: str, by_title: dict[str, dict[str, Any]], by_stem: dict[str, dict[str, Any]]) -> dict[str, Any] | None:
    return by_title.get(link) or by_stem.get(Path(link).stem)


def wiki_index(root: Path, wiki_root: str | None = None, tag: str | None = None, include_content: bool = False) -> dict[str, Any]:
    directory = wiki_root_path(root, wiki_root)
    if not directory.exists():
        return {"wiki_root": str(directory.relative_to(root)) if directory.is_relative_to(root) else str(directory), "pages": []}
    pages = [_page_entry(root, path, include_content) for path in sorted(directory.rglob("*.md")) if path.is_file()]
    by_title = {page["title"]: page for page in pages}
    by_stem = {Path(page["path"]).stem: page for page in pages}
    for page in pages:
        for link in page["links"]:
            target = _resolve_wikilink(link, by_title, by_stem)
            if target is not None and page["title"] not in target["backlinks"]:
                target["backlinks"].append(page["title"])
    if tag:
        pages = [page for page in pages if tag in page.get("tags", [])]
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
    return [part for part in Path(relative_path).parts if part.startswith(".") and part != ".wiki"]


def wiki_lint(root: Path, wiki_root: str | None = None) -> dict[str, Any]:
    directory = wiki_root_path(root, wiki_root)
    wiki_root_value = directory.relative_to(root).as_posix() if directory.exists() and directory.is_relative_to(root) else (directory.relative_to(root).as_posix() if directory.is_relative_to(root) else str(directory))
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
            errors.append(_lint_issue("missing_frontmatter", rel, "Missing required frontmatter: " + ", ".join(missing), fields=missing))
        page_type = meta.get("type")
        if isinstance(page_type, str) and page_type not in VALID_PAGE_TYPES:
            errors.append(_lint_issue("invalid_type", rel, f"Invalid frontmatter type: {page_type}", type=page_type))
        if not meta.get("summary"):
            warnings.append(_lint_issue("missing_summary", rel, "Missing frontmatter summary"))
        if not _tags(meta):
            warnings.append(_lint_issue("missing_tags", rel, "Missing frontmatter tags"))
        hidden_parts = _hidden_path_parts(rel)
        if hidden_parts:
            warnings.append(_lint_issue("hidden_path", rel, "Wiki page is under hidden path components: " + ", ".join(hidden_parts), parts=hidden_parts))
        if page_type == "module":
            package = meta.get("package")
            if isinstance(package, str) and package.strip():
                module_packages.setdefault(package.strip(), []).append(page)
            else:
                warnings.append(_lint_issue("module_missing_package", rel, "Module note is missing package frontmatter"))
            if not isinstance(meta.get("source_checkpoint"), str) or not str(meta.get("source_checkpoint")).strip():
                warnings.append(_lint_issue("module_missing_source_checkpoint", rel, "Module note is missing source_checkpoint frontmatter"))
            for line_number, line in enumerate(body.splitlines(), start=1):
                if LINE_LOCATOR_RE.search(line):
                    warnings.append(_lint_issue("module_line_locator", rel, "Module note appears to use a line-number locator", line=line_number))
                    break

    single_by_title = {title: items[0] for title, items in by_title.items() if len(items) == 1}
    single_by_stem = {stem: items[0] for stem, items in by_stem.items() if len(items) == 1}
    for title, items in sorted(by_title.items()):
        if len(items) > 1:
            errors.append(_lint_issue("duplicate_title", items[0]["path"], f"Duplicate wiki title: {title}", title=title, paths=[item["path"] for item in items]))
    for stem, items in sorted(by_stem.items()):
        if len(items) > 1 and stem != "index":
            errors.append(_lint_issue("duplicate_stem", items[0]["path"], f"Duplicate wiki file stem: {stem}", stem=stem, paths=[item["path"] for item in items]))
    for package, items in sorted(module_packages.items()):
        if len(items) > 1:
            errors.append(_lint_issue("duplicate_module_package", items[0]["path"], f"Duplicate module package: {package}", package=package, paths=[item["path"] for item in items]))
    for page in pages:
        for link in page["links"]:
            if _resolve_wikilink(link, single_by_title, single_by_stem) is None:
                errors.append(_lint_issue("broken_wikilink", page["path"], f"Broken wikilink: {link}", target=link))

    linked_paths: set[str] = set()
    for page in pages:
        for link in page["links"]:
            target = _resolve_wikilink(link, single_by_title, single_by_stem)
            if target is not None:
                linked_paths.add(target["path"])
    for page in pages:
        if page["path"] not in linked_paths and page["links"] == [] and Path(page["path"]).name != "index.md":
            warnings.append(_lint_issue("orphan_page", page["path"], "Page has no wikilinks or backlinks"))

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
        raise ArborError("wiki-search query must contain at least one token.")
    indexed = wiki_index(root, wiki_root, include_content=True)
    results: list[dict[str, Any]] = []
    weights = {
        "type": 20,
        "title": 8,
        "tags": 6,
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
            page_result["reason"] = "matched " + ", ".join(matched_fields)
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
                "tags": item.get("tags", []),
                "links": item.get("links", []),
                "backlinks": item.get("backlinks", []),
                "locators": item.get("locators", []),
                "score": item.get("score"),
                "reason": item.get("reason"),
            }
        )
    return {"wiki_root": search["wiki_root"], "query": query, "selected": selected}


def _strip_line_locator(value: str) -> str:
    value = re.sub(r":(?:L)?\d+(?=\b|$)", "", value.strip())
    return re.sub(r"\s+", " ", value).strip(" `")


def _split_field_items(value: str) -> list[str]:
    items: list[str] = []
    for raw in re.split(r"[\n,，、;；]", value):
        item = _strip_line_locator(raw.lstrip("- ").strip())
        if item and item not in items:
            items.append(item)
    return items


def _slice_progress(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    entries = data.get("slices")
    if not isinstance(entries, list):
        return {}
    return {item.get("id"): item for item in entries if isinstance(item, dict) and isinstance(item.get("id"), str)}


def _acceptance_by_slice(impl_result: dict[str, Any]) -> dict[str, list[str]]:
    coverage = impl_result.get("acceptance_coverage")
    if isinstance(coverage, dict):
        return {key: value for key, value in coverage.items() if isinstance(key, str) and isinstance(value, list)}
    return {}


def module_summary(root: Path, package: str, timestamp: str | None = None) -> dict[str, Any]:
    validate_name(package)
    pkg, data = load_package(root, package)
    execution = ensure_execution(data)
    errors = validate_package(root, package)
    prd_path = pkg / "prd.md"
    prd_slices, prd_errors = parse_prd_slices(prd_path.read_text(encoding="utf-8")) if prd_path.exists() else ([], [f"Missing PRD file: {prd_path}"])
    progress = _slice_progress(data)
    impl_result = data.get("impl_result") if isinstance(data.get("impl_result"), dict) else {}
    acceptance = _acceptance_by_slice(impl_result)
    slices = [
        {
            "id": item.id,
            "title": item.title,
            "status": progress.get(item.id, {}).get("status", "pending"),
            "completion_marker": item.completion_marker,
            "acceptance": acceptance.get(item.id, []),
        }
        for item in prd_slices
    ]
    contracts = [
        {
            "slice": item.id,
            "title": item.title,
            "completion_marker": item.completion_marker,
            "code_anchors": _split_field_items(item.code_anchors),
            "data_schema": _split_field_items(item.data_schema),
            "tests": _split_field_items(item.tests),
        }
        for item in prd_slices
    ]
    important_files: list[str] = []
    tests: list[str] = []
    for contract in contracts:
        for anchor in contract["code_anchors"]:
            if anchor and anchor not in important_files:
                important_files.append(anchor)
        for test in contract["tests"]:
            if test and test not in tests:
                tests.append(test)
    for command in impl_result.get("commands", []) if isinstance(impl_result.get("commands"), list) else []:
        if isinstance(command, str) and command not in tests:
            tests.append(command)
    check_ids = impl_result.get("checks", []) if isinstance(impl_result.get("checks"), list) else []
    for check in data.get("checks", []) if isinstance(data.get("checks"), list) else []:
        if not isinstance(check, dict) or check.get("id") not in check_ids:
            continue
        command = check.get("command")
        if isinstance(command, str) and command not in tests:
            tests.append(command)
    verification = [{"ok": not errors, "source": "validate_package", "errors": errors}]
    if prd_errors:
        verification.append({"ok": False, "source": "parse_prd_slices", "errors": prd_errors})
    if impl_result:
        verification.append({"ok": True, "source": "impl_result", "state": impl_result.get("state"), "commands": impl_result.get("commands", []), "checks": impl_result.get("checks", [])})
    return {
        "kind": "module-summary",
        "schema_version": "sdd-module-summary-v1",
        "package": package,
        "title": data.get("title") or package,
        "status": data.get("state"),
        "execution_status": execution.get("status"),
        "package_kind": data.get("package_kind", "single"),
        "important_files": important_files,
        "invariants": [],
        "slices": slices,
        "contracts": contracts,
        "tests": tests,
        "implementation": {
            "summary": impl_result.get("summary"),
            "state": impl_result.get("state"),
            "acceptance": impl_result.get("acceptance", []),
            "commands": impl_result.get("commands", []),
            "checks": impl_result.get("checks", []),
            "check_coverage": impl_result.get("check_coverage", {}),
            "concerns": impl_result.get("concerns", []),
        },
        "verification": verification,
        "related_packages": [],
    }
