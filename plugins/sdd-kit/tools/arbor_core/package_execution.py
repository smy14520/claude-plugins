from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import ArborError
from .fs import *
from .schema import *
from .state import ensure_execution
from .package_lifecycle import find_task


def claim_package(root: Path, name: str, owner: str, actor: str, note: str, timestamp: str, force: bool, branch: str | None, base_branch: str | None, worktree: str | None, session: str | None) -> dict[str, Any]:
    pkg, data = load_package(root, name)
    execution = ensure_execution(data)
    current_owner = execution.get("owner")
    if current_owner and current_owner != owner and not force:
        raise ArborError(f"Package already claimed by {current_owner}. Use --force to override.")
    execution["status"] = "claimed"
    execution["owner"] = owner
    execution["claimed_at"] = timestamp
    execution["released_at"] = None
    execution["updated_at"] = timestamp
    execution["updated_by"] = actor
    execution["note"] = note
    if session:
        execution["session"] = session
    if branch:
        execution["branch"]["name"] = branch
    if base_branch:
        execution["branch"]["base"] = base_branch
    if worktree:
        execution["worktree"]["path"] = worktree
    data["updated_at"] = timestamp
    save_package(pkg, data)
    return data


def release_package(root: Path, name: str, owner: str | None, actor: str, note: str, timestamp: str, force: bool) -> dict[str, Any]:
    pkg, data = load_package(root, name)
    execution = ensure_execution(data)
    current_owner = execution.get("owner")
    if owner and current_owner and current_owner != owner and not force:
        raise ArborError(f"Package claimed by {current_owner}, not {owner}. Use --force to release.")
    execution["status"] = "unclaimed"
    execution["owner"] = None
    execution["released_at"] = timestamp
    execution["updated_at"] = timestamp
    execution["updated_by"] = actor
    execution["note"] = note
    data["updated_at"] = timestamp
    save_package(pkg, data)
    return data


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


def record_checkpoint(root: Path, name: str, kind: str, sha: str, branch: str | None, base_sha: str | None, actor: str, note: str, timestamp: str) -> dict[str, Any]:
    if kind not in CHECKPOINT_KINDS:
        raise ArborError(f"Invalid checkpoint kind '{kind}'.")
    if not sha:
        raise ArborError("Checkpoint sha is required.")
    pkg, data = load_package(root, name)
    execution = ensure_execution(data)
    execution.setdefault("checkpoints", []).append(
        {
            "kind": kind,
            "sha": sha,
            "branch": branch,
            "base_sha": base_sha,
            "at": timestamp,
            "actor": actor,
            "note": note,
        }
    )
    execution["updated_at"] = timestamp
    execution["updated_by"] = actor
    execution["note"] = note
    data["updated_at"] = timestamp
    save_package(pkg, data)
    return data


def record_agent(root: Path, name: str, role: str, agent_name: str, status: str, summary: str, actor: str, note: str, timestamp: str, task_id: str | None) -> dict[str, Any]:
    if role not in AGENT_RECORD_ROLES:
        raise ArborError(f"Invalid agent role '{role}'.")
    if status not in AGENT_RECORD_STATUSES:
        raise ArborError(f"Invalid agent status '{status}'.")
    pkg, data = load_package(root, name)
    if task_id:
        find_task(data, task_id)
    execution = ensure_execution(data)
    execution.setdefault("agents", []).append(
        {
            "role": role,
            "name": agent_name,
            "status": status,
            "task_id": task_id,
            "at": timestamp,
            "summary": summary,
            "actor": actor,
            "note": note,
        }
    )
    execution["updated_at"] = timestamp
    execution["updated_by"] = actor
    execution["note"] = note
    data["updated_at"] = timestamp
    save_package(pkg, data)
    return data
