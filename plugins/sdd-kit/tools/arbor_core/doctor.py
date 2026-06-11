from __future__ import annotations

from pathlib import Path
from typing import Any

from .package_queries import list_packages
from .validation import validate_package


def _validate_packages(root: Path) -> dict[str, Any]:
    errors: dict[str, list[str]] = {}
    packages = list_packages(root)
    active_packages = [item for item in packages if item.get("state") != "archived"]
    for item in active_packages:
        name = item.get("name")
        if not isinstance(name, str):
            continue
        package_errors = validate_package(root, name)
        if package_errors:
            errors[name] = package_errors
    return {"ok": not errors, "errors": errors, "count": len(active_packages), "items": active_packages, "archived_count": len(packages) - len(active_packages)}


def _next_action(packages: list[dict[str, Any]], errors: dict[str, list[str]]) -> dict[str, Any]:
    if errors:
        return {"skill": "doctor", "package": next(iter(errors)), "reason": "先修复 package validation errors"}
    for skill in ["brainstorm", "impl", "review", "user"]:
        for item in packages:
            next_action = item.get("next_action") if isinstance(item.get("next_action"), dict) else {}
            if next_action.get("skill") == skill:
                return {"skill": skill, "package": item.get("name"), "reason": next_action.get("reason")}
    return {"skill": "none", "package": None, "reason": "没有待推进的 package"}


def doctor(root: Path, timestamp: str = "") -> dict[str, Any]:
    """Check `.arbor` package health. Wiki health lives in `sdd-wiki lint`."""
    packages = _validate_packages(root)
    package_error_count = sum(len(errors) for errors in packages["errors"].values())
    next_action = _next_action(packages.get("items", []), packages["errors"])
    blocked_count = sum(
        1
        for item in packages.get("items", [])
        if isinstance(item.get("next_action"), dict) and item["next_action"].get("skill") == "user"
    )
    summary = {
        "error_count": package_error_count,
        "warning_count": 0,
        "blocked_count": blocked_count,
    }
    return {
        "ok": packages["ok"],
        "packages": packages,
        "summary": summary,
        "next_action": next_action,
    }
