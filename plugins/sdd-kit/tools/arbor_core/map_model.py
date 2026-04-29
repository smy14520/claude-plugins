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
            "strategy": "serial-package-map",
            "dependency_gate": "下游 package 只依赖明确完成或 merged 的上游 package；map-check 只报告串行下一步和 blocker。",
            "execution_model": "map 负责 package graph / dependency navigation，不自动创建 Team、不派 worker。",
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
    directory.mkdir(parents=True, exist_ok=True)
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
        defaults = base_map_json(initiative, title, timestamp)["orchestration"]
        orchestration = data.setdefault("orchestration", {})
        if not isinstance(orchestration, dict):
            orchestration = {}
            data["orchestration"] = orchestration
        orchestration["strategy"] = "serial-package-map"
        for key, value in defaults.items():
            orchestration.setdefault(key, value)
        for legacy_key in ["runtime", "default_max_parallel", "execution_isolation", "context_injection", "write_permission_boundary", "contract_boundary", "mainline_boundary", "integration_boundary", "manual_review_mode"]:
            orchestration.pop(legacy_key, None)
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

    return {"initiative": initiative, "map": parent_map_ref(initiative), "map_json": f".arbor/maps/{initiative}/map.json", "created": created}


def ensure_map_workspace(root: Path, initiative: str, timestamp: str) -> dict[str, Any]:
    if map_path(root, initiative).exists():
        return create_map(root, initiative, initiative, timestamp, status=None)
    if legacy_map_path(root, initiative).exists():
        return create_map(root, initiative, initiative, timestamp, status=None)
    raise ArborError(f"Missing initiative map: {map_path(root, initiative)}")
