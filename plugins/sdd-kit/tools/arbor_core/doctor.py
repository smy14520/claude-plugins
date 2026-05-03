from __future__ import annotations

from pathlib import Path
from typing import Any

from .package_queries import list_packages
from .validation import validate_package
from .wiki_state import wiki_lint, wiki_root_path


def _validate_packages(root: Path) -> dict[str, Any]:
    errors: dict[str, list[str]] = {}
    packages = list_packages(root)
    for item in packages:
        name = item.get("name")
        if not isinstance(name, str):
            continue
        package_errors = validate_package(root, name)
        if package_errors:
            errors[name] = package_errors
    return {"ok": not errors, "errors": errors, "count": len(packages), "items": packages}


def _next_action(packages: list[dict[str, Any]], errors: dict[str, list[str]]) -> dict[str, Any]:
    if errors:
        return {"skill": "doctor", "package": next(iter(errors)), "reason": "先修复 package validation errors"}
    for skill in ["brainstorm", "impl", "review", "user"]:
        for item in packages:
            next_action = item.get("next_action") if isinstance(item.get("next_action"), dict) else {}
            if next_action.get("skill") == skill:
                return {"skill": skill, "package": item.get("name"), "reason": next_action.get("reason")}
    return {"skill": "none", "package": None, "reason": "没有待推进的 package"}


def _lint_wiki(root: Path, wiki_root: str) -> dict[str, Any]:
    directory = wiki_root_path(root, wiki_root)
    if not directory.exists():
        wiki_root_value = directory.relative_to(root).as_posix() if directory.is_relative_to(root) else str(directory)
        return {"ok": True, "skipped": True, "wiki_root": wiki_root_value, "errors": [], "warnings": [], "summary": {"error_count": 0, "warning_count": 0}}
    result = wiki_lint(root, wiki_root)
    result["skipped"] = False
    return result


def doctor(root: Path, wiki_root: str = ".wiki", timestamp: str = "") -> dict[str, Any]:
    packages = _validate_packages(root)
    wiki = _lint_wiki(root, wiki_root)
    package_error_count = sum(len(errors) for errors in packages["errors"].values())
    wiki_summary = wiki.get("summary", {}) if isinstance(wiki.get("summary"), dict) else {}
    next_action = _next_action(packages.get("items", []), packages["errors"])
    blocked_count = sum(
        1
        for item in packages.get("items", [])
        if isinstance(item.get("next_action"), dict) and item["next_action"].get("skill") == "user"
    )
    summary = {
        "error_count": package_error_count + int(wiki_summary.get("error_count", 0)),
        "warning_count": int(wiki_summary.get("warning_count", 0)),
        "blocked_count": blocked_count,
    }
    return {
        "ok": packages["ok"] and wiki["ok"],
        "packages": packages,
        "wiki": wiki,
        "summary": summary,
        "next_action": next_action,
    }
