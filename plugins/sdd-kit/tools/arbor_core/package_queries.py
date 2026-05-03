from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import ArborError
from .fs import *
from .validation import validate_package


def list_packages(root: Path) -> list[dict[str, Any]]:
    root_dir = tasks_root(root)
    if not root_dir.exists():
        return []
    result: list[dict[str, Any]] = []
    for pkg in sorted(path for path in root_dir.iterdir() if path.is_dir()):
        task_path = pkg / "task.json"
        if not task_path.exists():
            continue
        try:
            data = read_json(task_path)
        except ArborError:
            continue
        execution = data.get("execution") if isinstance(data.get("execution"), dict) else {}
        branch = execution.get("branch") if isinstance(execution.get("branch"), dict) else {}
        worktree = execution.get("worktree") if isinstance(execution.get("worktree"), dict) else {}
        pr = execution.get("pr") if isinstance(execution.get("pr"), dict) else {}
        sizing = data.get("package_sizing") if isinstance(data.get("package_sizing"), dict) else {}
        result.append(
            {
                "name": pkg.name,
                "state": data.get("state"),
                "current_phase": data.get("current_phase"),
                "package_sizing": sizing.get("status"),
                "next_action": data.get("next_action"),
                "execution_status": execution.get("status"),
                "execution_owner": execution.get("owner"),
                "branch": branch.get("name"),
                "worktree": worktree.get("path"),
                "pr": pr.get("url") or pr.get("number"),
            }
        )
    return result


def show_package(root: Path, name: str) -> dict[str, Any]:
    pkg, data = load_package(root, name)
    errors = validate_package(root, name)
    return {
        "name": name,
        "package": str(pkg),
        "state": data.get("state"),
        "current_phase": data.get("current_phase"),
        "next_action": data.get("next_action"),
        "execution": data.get("execution"),
        "package_sizing": data.get("package_sizing"),
        "prd": data.get("prd"),
        "impl_result": data.get("impl_result"),
        "review_result": data.get("review_result"),
        "validation": {"ok": not errors, "errors": errors},
    }
