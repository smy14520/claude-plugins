from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import ArborError
from .fs import *
from .schema import *
from .state import default_execution
from .templates import prd_template, review_template, task_template


def base_task_json(name: str, mode: str, title: str, timestamp: str, source_type: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "name": name,
        "title": title,
        "package_path": f".arbor/tasks/{name}",
        "created_at": timestamp,
        "updated_at": timestamp,
        "completed_at": None,
        "prd": {
            "file": "prd.md",
            "status": "draft",
            "source_type": source_type,
            "legacy_source": f".arbor/brainstorms/{name}.md" if source_type == "legacy-brainstorm" else None,
            "ready_for_task_at": None,
            "amendments": [],
        },
        "definition": {
            "task_md": "task.md",
            "frozen": False,
            "version": 0,
            "updated_at": None,
        },
        "package_sizing": {
            "status": "unchecked",
            "decision": None,
            "signals": [],
            "recommended_packages": [],
            "decided_at": None,
            "decided_by": None,
            "note": None,
        },
        "mode": mode,
        "state": "planned",
        "current_phase": "brainstorm",
        "active_task": None,
        "next_action": {
            "skill": "brainstorm",
            "task_id": None,
            "reason": "PRD 草稿已创建，下一步由 brainstorm 补齐 package-local 需求与方案 framing",
        },
        "execution": default_execution(name),
        "tasks": [],
        "phase_history": [
            {
                "at": timestamp,
                "phase": "brainstorm",
                "task_id": None,
                "from": None,
                "to": "planned",
                "actor": "arbor",
                "note": "task package 已创建",
            }
        ],
    }


def create_package(root: Path, name: str, mode: str, title: str | None, source_type: str, timestamp: str) -> dict[str, Any]:
    validate_name(name)
    if mode not in MODES:
        raise ArborError(f"Invalid mode '{mode}'. Expected one of: {', '.join(sorted(MODES))}.")
    if source_type not in {"new", "legacy-brainstorm", "ad-hoc", "map-split"}:
        raise ArborError("Invalid source type. Expected new, legacy-brainstorm, ad-hoc, or map-split.")

    title = title or name
    pkg = package_dir(root, name)
    context_dir = pkg / "context"
    context_dir.mkdir(parents=True, exist_ok=True)

    created_files: list[str] = []
    for rel, content in [
        ("prd.md", prd_template(name, title, timestamp)),
        ("task.md", task_template(name, mode, timestamp)),
        ("review.md", review_template(name, timestamp)),
        ("context/impl.jsonl", ""),
        ("context/review.jsonl", ""),
        ("context/sources.jsonl", ""),
    ]:
        if write_if_missing(pkg / rel, content):
            created_files.append(rel)

    task_path = task_json_path(pkg)
    if task_path.exists():
        data = read_json(task_path)
    else:
        data = base_task_json(name, mode, title, timestamp, source_type)
        write_json(task_path, data)
        created_files.append("task.json")

    return {"package": str(pkg), "created": created_files, "already_exists": not bool(created_files)}
