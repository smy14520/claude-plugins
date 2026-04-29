from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import ArborError
from .fs import *
from .schema import *
from .templates import map_template


def base_map_json(initiative: str, title: str, timestamp: str) -> dict[str, Any]:
    return {
        "schema_version": MAP_SCHEMA_VERSION,
        "initiative": initiative,
        "title": title,
        "map_path": parent_map_ref(initiative),
        "status": "draft",
        "created_at": timestamp,
        "updated_at": timestamp,
        "packages": [],
        "contract_requests": [],
        "orchestration": {
            "default_max_parallel": 3,
            "strategy": "lead-owned-rolling-worker-pool",
            "runtime": "claude-code-agent-team",
            "dependency_gate": "由 map-time parallel_policy 决定依赖未完成时是否允许先做准备；impl/review 必须等 dependency gate 满足",
            "execution_isolation": "Agent Team teammate 必须先 EnterWorktree 到 package worktree 并验证 cwd/git root/branch，WORKTREE_READY 前不得读写",
            "context_injection": "注入 map.md、map.json、worker-dispatch.md、package task.json/prd/task/context 以及依赖摘要",
            "write_permission_boundary": "package worker 只能修改声明的 modification_scope；shared/global 路径属于 serial integration worker scope，不由 lead session 直接实现",
            "contract_boundary": "跨 package 需求通过 contract_outputs/contract_inputs/contract_requests 表达，不互改 sibling internals",
            "mainline_boundary": "worker 只通过 lead mainline checkpoint 同步，不读取或合并 sibling branches/worktrees",
            "integration_boundary": "shared center files/global wiring/DI/routes/migrations/E2E 进入 lead-owned serial integration worker lane；lead 只审查/checkpoint",
            "manual_review_mode": "需要人工 gate 时显式使用 brainstorm/task/impl/review skills，而不是 parallel",
        },
        "history": [
            {
                "at": timestamp,
                "actor": "arbor",
                "event": "map_created",
                "note": "initiative map workspace 已创建",
            }
        ],
    }


def create_map(root: Path, initiative: str, title: str | None, timestamp: str, status: str | None = "draft") -> dict[str, Any]:
    validate_name(initiative)
    if status is not None and status not in {"draft", "active", "ready", "closed", "superseded"}:
        raise ArborError(f"Invalid map status '{status}'.")
    title = title or initiative
    directory = map_dir(root, initiative)
    context_dir = map_context_dir(root, initiative)
    context_dir.mkdir(parents=True, exist_ok=True)
    created: list[str] = []

    md_path = map_path(root, initiative)
    legacy_path = legacy_map_path(root, initiative)
    if not md_path.exists():
        if legacy_path.exists():
            md_path.write_text(legacy_path.read_text(encoding="utf-8"), encoding="utf-8")
        else:
            md_path.write_text(map_template(initiative, title, timestamp), encoding="utf-8")
        created.append("map.md")

    json_path = map_json_path(root, initiative)
    if json_path.exists():
        data = read_json(json_path)
        data.setdefault("schema_version", MAP_SCHEMA_VERSION)
        data.setdefault("initiative", initiative)
        data.setdefault("title", title)
        data.setdefault("map_path", parent_map_ref(initiative))
        data.setdefault("packages", [])
        orchestration = data.setdefault("orchestration", base_map_json(initiative, title, timestamp)["orchestration"])
        if isinstance(orchestration, dict):
            defaults = base_map_json(initiative, title, timestamp)["orchestration"]
            for key, value in defaults.items():
                orchestration.setdefault(key, value)
            if orchestration.get("strategy") in {"ready-packages-only", "autonomous-package-pipeline", "agent-team-worktree-pipeline"}:
                orchestration["strategy"] = "lead-owned-rolling-worker-pool"
            if orchestration.get("default_max_parallel") == 2:
                orchestration["default_max_parallel"] = 3
            orchestration.setdefault("runtime", "claude-code-agent-team")
            orchestration.setdefault("execution_isolation", "Agent Team teammate must explicitly EnterWorktree and verify before touching files")
        if not isinstance(data.get("contract_requests"), list):
            data["contract_requests"] = []
        else:
            data.setdefault("contract_requests", [])
        data.setdefault("history", [])
        if status is not None:
            data["status"] = status
        else:
            data.setdefault("status", "draft")
        data["updated_at"] = timestamp
    else:
        data = base_map_json(initiative, title, timestamp)
        data["status"] = status
        created.append("map.json")
    write_json(json_path, data)

    assignments_path = context_dir / "agent-assignments.jsonl"
    if write_if_missing(assignments_path, ""):
        created.append("context/agent-assignments.jsonl")

    return {"initiative": initiative, "map": parent_map_ref(initiative), "map_json": f".arbor/maps/{initiative}/map.json", "created": created}


def ensure_map_workspace(root: Path, initiative: str, timestamp: str) -> dict[str, Any]:
    if map_path(root, initiative).exists():
        return create_map(root, initiative, initiative, timestamp, status=None)
    if legacy_map_path(root, initiative).exists():
        return create_map(root, initiative, initiative, timestamp, status=None)
    raise ArborError(f"Missing initiative map: {map_path(root, initiative)}")
