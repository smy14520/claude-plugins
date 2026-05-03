from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import ArborError
from .fs import load_package, save_package
from .schema import EXECUTION_STATUSES, PR_STATES
from .state import ensure_execution


def set_execution(root: Path, name: str, status: str | None, actor: str, note: str, timestamp: str, base_branch: str | None, branch: str | None, upstream: str | None, worktree: str | None, worktree_created_by: str | None) -> dict[str, Any]:
    pkg, data = load_package(root, name)
    execution = ensure_execution(data)
    if status:
        if status not in EXECUTION_STATUSES:
            raise ArborError(f"Invalid execution status '{status}'.")
        execution["status"] = status
    if base_branch:
        execution["branch"]["base"] = base_branch
    if branch:
        execution["branch"]["name"] = branch
    if upstream:
        execution["branch"]["upstream"] = upstream
    if worktree:
        execution["worktree"]["path"] = worktree
    if worktree_created_by:
        execution["worktree"]["created_by"] = worktree_created_by
    execution["updated_at"] = timestamp
    execution["updated_by"] = actor
    execution["note"] = note
    data["updated_at"] = timestamp
    save_package(pkg, data)
    return data


def set_pr(root: Path, name: str, actor: str, note: str, timestamp: str, url: str | None, number: int | None, state: str | None) -> dict[str, Any]:
    pkg, data = load_package(root, name)
    execution = ensure_execution(data)
    pr = execution.setdefault("pr", {"url": None, "number": None, "state": "none"})
    if url:
        pr["url"] = url
    if number is not None:
        pr["number"] = number
    if state:
        if state not in PR_STATES:
            raise ArborError(f"Invalid PR state '{state}'.")
        pr["state"] = state
        if state == "open":
            execution["status"] = "pr_open"
        elif state == "merged":
            execution["status"] = "merged"
    execution["updated_at"] = timestamp
    execution["updated_by"] = actor
    execution["note"] = note
    data["updated_at"] = timestamp
    save_package(pkg, data)
    return data
