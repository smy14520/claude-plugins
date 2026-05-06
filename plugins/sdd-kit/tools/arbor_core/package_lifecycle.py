from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .errors import ArborError
from .fs import *
from .schema import *
from .state import add_phase_history, route_package_state

_FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---(\r?\n|\Z)", re.DOTALL)
_FRONTMATTER_STATUS_LINE_RE = re.compile(r"^(status:[ \t]*)(\S+)([ \t]*.*)$", re.MULTILINE)


def _sync_prd_markdown_status(root: Path, name: str, status: str) -> None:
    """Best-effort sync of the prd.md YAML frontmatter `status:` field.

    Keeps PRD metadata aligned with task.json so reviewers reading prd.md
    don't see `status: draft` after brainstorm finalize. No-op when prd.md
    is missing, lacks a YAML frontmatter block, or has no `status:` line —
    legacy or hand-written PRDs without frontmatter remain untouched.
    """
    prd_path = package_dir(root, name) / "prd.md"
    if not prd_path.exists():
        return
    text = prd_path.read_text(encoding="utf-8")
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return
    frontmatter = match.group(1)
    updated, count = _FRONTMATTER_STATUS_LINE_RE.subn(
        lambda m: f"{m.group(1)}{status}{m.group(3)}",
        frontmatter,
        count=1,
    )
    if count == 0 or updated == frontmatter:
        return
    rest = text[match.end():]
    prd_path.write_text(
        f"---\n{updated}\n---{match.group(2)}{rest}",
        encoding="utf-8",
    )


def update_package_status(root: Path, name: str, state: str, actor: str, note: str, timestamp: str) -> dict[str, Any]:
    from .schema import LEGACY_STATE_MAP
    resolved = LEGACY_STATE_MAP.get(state, state)
    if resolved not in TOP_LEVEL_STATES:
        raise ArborError(f"Invalid package state '{state}'.")
    pkg, data = load_package(root, name)
    old = data.get("state")
    route_package_state(data, resolved, timestamp, actor, note)
    add_phase_history(data, timestamp, data.get("current_phase", "impl"), old, resolved, actor, note)
    save_package(pkg, data)
    return data


def infer_sizing_phase(data: dict[str, Any], actor: str, phase: str | None) -> str:
    if phase:
        if phase not in PHASES:
            raise ArborError(f"Invalid package sizing phase '{phase}'.")
        return phase
    if actor == "brainstorm":
        return actor
    current_phase = data.get("current_phase")
    return current_phase if current_phase in PHASES else "brainstorm"


def set_package_sizing(root: Path, name: str, status: str, actor: str, note: str, timestamp: str, decision: str | None, signals: list[str], recommended_packages: list[str], phase: str | None = None) -> dict[str, Any]:
    if status not in PACKAGE_SIZING_STATUSES:
        raise ArborError(f"Invalid package sizing status '{status}'.")
    pkg, data = load_package(root, name)
    sizing_phase = infer_sizing_phase(data, actor, phase)
    recommended: list[dict[str, Any]] = []
    for raw in recommended_packages:
        parts = raw.split(":", 1)
        package_name = parts[0].strip()
        if not NAME_RE.match(package_name):
            raise ArborError(f"Invalid recommended package name '{package_name}'.")
        reason = parts[1].strip() if len(parts) == 2 else ""
        recommended.append({"name": package_name, "reason": reason})
    old = data.get("package_sizing", {}).get("status") if isinstance(data.get("package_sizing"), dict) else None
    data["package_sizing"] = {
        "status": status,
        "decision": decision,
        "signals": signals,
        "recommended_packages": recommended,
        "decided_at": timestamp,
        "decided_by": actor,
        "note": note,
    }
    data["package_kind"] = "single"
    data["updated_at"] = timestamp
    add_phase_history(data, timestamp, sizing_phase, old, f"package_sizing:{status}", actor, note)
    save_package(pkg, data)
    return data


def update_phase(root: Path, name: str, phase: str, actor: str, note: str, timestamp: str) -> dict[str, Any]:
    if phase not in PHASES:
        raise ArborError(f"Invalid phase '{phase}'.")
    pkg, data = load_package(root, name)
    old = data.get("current_phase")
    data["current_phase"] = phase
    data["updated_at"] = timestamp
    add_phase_history(data, timestamp, phase, old, phase, actor, note)
    save_package(pkg, data)
    return data


def update_prd_status(root: Path, name: str, status: str, actor: str, note: str, timestamp: str) -> dict[str, Any]:
    if status not in {"draft", "ready", "revising", "superseded"}:
        raise ArborError(f"Invalid PRD status '{status}'.")
    pkg, data = load_package(root, name)
    prd = data.setdefault("prd", {})
    old = prd.get("status")
    if status == "ready":
        sizing = data.get("package_sizing") if isinstance(data.get("package_sizing"), dict) else {}
        sizing_status = sizing.get("status")
        if sizing_status == "unchecked":
            raise ArborError("Cannot mark PRD ready before brainstorm records package sizing as fits_package.")
        if sizing_status != "fits_package":
            raise ArborError("Cannot mark PRD ready without package_sizing.status fits_package.")
    prd["status"] = status
    if status == "ready":
        prd["ready_at"] = timestamp
        route_package_state(data, "ready", timestamp, actor, note)
    elif status in {"draft", "revising"}:
        data["current_phase"] = "brainstorm"
        data["next_action"] = {"skill": "brainstorm", "reason": "PRD 尚未就绪，不能进入 impl"}
    elif status == "superseded":
        route_package_state(data, "superseded", timestamp, actor, note)
    data["updated_at"] = timestamp
    add_phase_history(data, timestamp, data.get("current_phase", "brainstorm"), old, status, actor, note)
    save_package(pkg, data)
    _sync_prd_markdown_status(root, name, status)
    return data


def amendment_ids(data: dict[str, Any]) -> set[str]:
    prd = data.setdefault("prd", {})
    amendments = prd.setdefault("amendments", [])
    if not isinstance(amendments, list):
        raise ArborError("prd.amendments must be an array.")
    return {item.get("id") for item in amendments if isinstance(item, dict) and isinstance(item.get("id"), str)}


def next_amendment_id(data: dict[str, Any]) -> str:
    existing = amendment_ids(data)
    index = 1
    while True:
        candidate = f"AMD-{index:03d}"
        if candidate not in existing:
            return candidate
        index += 1


def add_amendment(root: Path, name: str, amendment_id: str | None, title: str, wrong: str, correct: str, affects: list[str], source: str, actor: str, timestamp: str) -> dict[str, Any]:
    pkg, data = load_package(root, name)
    prd = data.setdefault("prd", {})
    amendments = prd.setdefault("amendments", [])
    if not isinstance(amendments, list):
        raise ArborError("prd.amendments must be an array.")
    amendment_id = amendment_id or next_amendment_id(data)
    if not AMENDMENT_ID_RE.match(amendment_id):
        raise ArborError(f"Invalid amendment id '{amendment_id}'. Use AMD-001 format.")
    if amendment_id in amendment_ids(data):
        raise ArborError(f"Amendment already exists: {amendment_id}")
    amendments.append({
        "id": amendment_id,
        "title": title,
        "wrong": wrong,
        "correct": correct,
        "affects": affects,
        "source": source,
        "created_at": timestamp,
        "created_by": actor,
    })
    prd["status"] = "ready"
    prd["ready_at"] = timestamp
    route_package_state(data, "ready", timestamp, actor, title)
    data["current_phase"] = "brainstorm"
    data["next_action"] = {"skill": "impl", "reason": f"amendment {amendment_id} 已记录，按更新后的 PRD scope 执行"}
    add_phase_history(data, timestamp, "brainstorm", None, f"amendment:{amendment_id}", actor, title)
    save_package(pkg, data)
    _sync_prd_markdown_status(root, name, "ready")
    return data
