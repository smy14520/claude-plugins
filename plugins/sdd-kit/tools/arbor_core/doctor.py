from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import ArborError
from .fs import maps_root, read_json
from .map_readiness import map_check
from .package_queries import list_packages
from .validation import validate_package
from .wiki_state import wiki_lint, wiki_root_path


def _map_initiatives(root: Path) -> list[str]:
    directory = maps_root(root)
    if not directory.exists():
        return []
    initiatives: list[str] = []
    for path in sorted(item for item in directory.iterdir() if item.is_dir()):
        if (path / "map.json").exists():
            initiatives.append(path.name)
    return initiatives


def _validate_tasks(root: Path) -> dict[str, Any]:
    errors: dict[str, list[str]] = {}
    for item in list_packages(root):
        name = item.get("name")
        if not isinstance(name, str):
            continue
        package_errors = validate_package(root, name)
        if package_errors:
            errors[name] = package_errors
    return {"ok": not errors, "errors": errors, "count": len(list_packages(root))}


def _lint_wiki(root: Path, wiki_root: str) -> dict[str, Any]:
    directory = wiki_root_path(root, wiki_root)
    if not directory.exists():
        wiki_root_value = directory.relative_to(root).as_posix() if directory.is_relative_to(root) else str(directory)
        return {"ok": True, "skipped": True, "wiki_root": wiki_root_value, "errors": [], "warnings": [], "summary": {"error_count": 0, "warning_count": 0}}
    result = wiki_lint(root, wiki_root)
    result["skipped"] = False
    return result


def _check_maps(root: Path, timestamp: str) -> dict[str, Any]:
    initiatives: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    blocked_count = 0
    for initiative in _map_initiatives(root):
        try:
            read_json(maps_root(root) / initiative / "map.json")
            result = map_check(root, initiative, timestamp)
        except ArborError as exc:
            errors.append({"initiative": initiative, "message": str(exc)})
            continue
        blocked = result.get("blocked", []) if isinstance(result.get("blocked"), list) else []
        missing = result.get("missing", []) if isinstance(result.get("missing"), list) else []
        blocked_count += len(blocked) + len(missing)
        initiatives.append(
            {
                "initiative": initiative,
                "ready_count": len(result.get("ready", [])) if isinstance(result.get("ready"), list) else 0,
                "blocked_count": len(blocked),
                "active_count": len(result.get("active", [])) if isinstance(result.get("active"), list) else 0,
                "complete_count": len(result.get("complete", [])) if isinstance(result.get("complete"), list) else 0,
                "missing_count": len(missing),
                "blocked": blocked,
                "missing": missing,
            }
        )
    return {"ok": not errors, "initiatives": initiatives, "errors": errors, "blocked_count": blocked_count}


def doctor(root: Path, wiki_root: str = ".wiki", timestamp: str = "") -> dict[str, Any]:
    tasks = _validate_tasks(root)
    wiki = _lint_wiki(root, wiki_root)
    maps = _check_maps(root, timestamp)
    task_error_count = sum(len(errors) for errors in tasks["errors"].values())
    wiki_summary = wiki.get("summary", {}) if isinstance(wiki.get("summary"), dict) else {}
    summary = {
        "error_count": task_error_count + int(wiki_summary.get("error_count", 0)) + len(maps.get("errors", [])),
        "warning_count": int(wiki_summary.get("warning_count", 0)),
        "blocked_count": int(maps.get("blocked_count", 0)),
    }
    return {
        "ok": tasks["ok"] and wiki["ok"] and maps["ok"],
        "tasks": tasks,
        "wiki": wiki,
        "maps": maps,
        "summary": summary,
    }
