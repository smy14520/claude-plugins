from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .errors import ArborError
from .fs import load_package, save_package
from .package_checks import ensure_required_checks
from .package_lifecycle import update_package_status
from .slice_defs import slice_defs

_WIKI_PATH_RE = re.compile(r"\.wiki/[^\s)\]`\"']+")

# PRD sections the impl agent reads itself; the packet only points at them
# instead of parsing markdown semantics (source of truth stays in prd.md).
_PRD_READ_ANCHORS = ["prd.md#Technical Framing", "prd.md#关键约束（仅保留承重约束）"]


def _read_next(pkg: Path) -> list[str]:
    items = list(_PRD_READ_ANCHORS)
    artifacts = pkg / "artifacts"
    if artifacts.is_dir():
        items.extend(f"artifacts/{path.name}" for path in sorted(artifacts.iterdir()) if path.is_file())
    prd_path = pkg / "prd.md"
    if prd_path.exists():
        items.extend(sorted(set(_WIKI_PATH_RE.findall(prd_path.read_text(encoding="utf-8")))))
    return items


def _ensure_required_checks_saved(pkg: Path, data: dict[str, Any], timestamp: str) -> list[dict[str, Any]]:
    existing = data.get("required_checks")
    required = ensure_required_checks(pkg, data, timestamp)
    if required is not existing:
        save_package(pkg, data)
    return required


def _slice_entries(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {entry.get("id"): entry for entry in data.get("slices", []) if isinstance(entry, dict)}


def _prior(data: dict[str, Any], slice_id: str | None) -> dict[str, Any]:
    entries = _slice_entries(data)
    done_ids = sorted(sid for sid, entry in entries.items() if isinstance(sid, str) and entry.get("status") == "done")
    impl_result = data.get("impl_result") if isinstance(data.get("impl_result"), dict) else {}
    checks = data.get("checks") if isinstance(data.get("checks"), list) else []
    failed_checks = [
        {"id": entry.get("id"), "command": entry.get("command"), "slice": entry.get("slice")}
        for entry in checks
        if isinstance(entry, dict) and entry.get("status") == "failed" and (slice_id is None or entry.get("slice") == slice_id)
    ]
    return {
        "last_done_slice": done_ids[-1] if done_ids else None,
        "concerns": impl_result.get("concerns", []),
        "failed_checks": failed_checks,
    }


def impl_packet(root: Path, name: str, slice_id: str | None, timestamp: str) -> dict[str, Any]:
    """Deterministic execution packet for impl: one command instead of a reading list."""
    pkg, data = load_package(root, name)
    next_action = data.get("next_action") if isinstance(data.get("next_action"), dict) else {}
    if slice_id is None and (data.get("state") == "ready" or next_action.get("skill") == "impl"):
        update_package_status(root, name, "doing", "impl", "开始执行", timestamp)
        pkg, data = load_package(root, name)
    prd_slices = slice_defs(pkg, data)
    required = _ensure_required_checks_saved(pkg, data, timestamp)
    entries = _slice_entries(data)
    execution = data.get("execution") if isinstance(data.get("execution"), dict) else {}

    if slice_id is None:
        statuses = [
            {
                "id": item.id,
                "title": item.title,
                "status": entries.get(item.id, {}).get("status", "pending"),
                "note": entries.get(item.id, {}).get("note", ""),
            }
            for item in prd_slices
        ]
        next_slice = next((row["id"] for row in statuses if row["status"] != "done"), None)
        return {
            "kind": "impl-packet",
            "package": name,
            "state": data.get("state"),
            "next_action": data.get("next_action"),
            "base_ref": execution.get("base_ref"),
            "base_ref_dirty": execution.get("base_ref_dirty", False),
            "slices": statuses,
            "next_slice": next_slice,
            "read_next": _read_next(pkg),
        }

    slice_item = next((item for item in prd_slices if item.id == slice_id), None)
    if slice_item is None:
        raise ArborError(f"Slice id '{slice_id}' is not defined in PRD ## Slices.")
    task_file = pkg / "slices" / f"{slice_id}.md"
    if not task_file.exists():
        raise ArborError(f"Missing slice task file: {task_file}. Brainstorm must create slices/{slice_id}.md before impl.")
    return {
        "kind": "impl-packet",
        "package": name,
        "slice": {
            "id": slice_item.id,
            "title": slice_item.title,
            "status": entries.get(slice_id, {}).get("status", "pending"),
            "task_file": f"slices/{slice_id}.md",
            "task_content": task_file.read_text(encoding="utf-8"),
            "markers": slice_item.marker_ids(),
            "completion_markers": list(slice_item.completion_markers),
        },
        "required_checks": [item for item in required if item.get("slice") == slice_id],
        "prior": _prior(data, slice_id),
        "read_next": _read_next(pkg),
    }
