from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .errors import ArborError
from .fs import *
from .schema import *
from .package_lifecycle import find_task


def _context_path(root: Path, name: str, context_type: str) -> Path:
    if context_type not in CONTEXT_TYPES:
        raise ArborError(f"Invalid context type '{context_type}'.")
    return package_dir(root, name) / "context" / f"{context_type}.jsonl"


def _normalize_context_line(context_type: str, entry: dict[str, Any], actor: str, timestamp: str) -> tuple[dict[str, Any], list[str]]:
    if context_type == "sources":
        return entry, []
    fields: list[str] = []
    normalized = dict(entry)
    if not normalized.get("kind"):
        normalized["kind"] = "note"
        fields.append("kind")
    if not normalized.get("at"):
        normalized["at"] = timestamp
        fields.append("at")
    if not normalized.get("actor"):
        normalized["actor"] = actor
        fields.append("actor")
    if "task_id" not in normalized:
        normalized["task_id"] = None
        fields.append("task_id")
    return normalized, fields


def repair_context_jsonl(root: Path, name: str, context_type: str, actor: str, timestamp: str) -> dict[str, Any]:
    validate_name(name)
    path = _context_path(root, name, context_type)
    if not path.exists():
        raise ArborError(f"Missing context file: {path}")
    repaired: list[dict[str, Any]] = []
    entries: list[dict[str, Any]] = []
    changed = False
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            entry = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ArborError(f"Invalid JSONL at {path}:{line_no}: {exc}") from exc
        if not isinstance(entry, dict):
            raise ArborError(f"JSONL entry must be an object at {path}:{line_no}")
        normalized, fields = _normalize_context_line(context_type, entry, actor, timestamp)
        if fields:
            repaired.append({"line": line_no, "fields": fields})
            changed = True
        entries.append(normalized)
    if changed:
        path.write_text("".join(json.dumps(entry, ensure_ascii=False, separators=(",", ":")) + "\n" for entry in entries), encoding="utf-8")
        pkg, data = load_package(root, name)
        data["updated_at"] = timestamp
        save_package(pkg, data)
    return {"package": name, "type": context_type, "changed": changed, "repaired": repaired, "count": len(repaired)}


def add_context(root: Path, name: str, context_type: str, task_id: str | None, kind: str | None, summary: str | None, source: str | None, actor: str, timestamp: str, source_id: str | None, source_type: str | None, location: str | None, title: str | None, why: str | None) -> dict[str, Any]:
    if context_type not in CONTEXT_TYPES:
        raise ArborError(f"Invalid context type '{context_type}'.")
    pkg, data = load_package(root, name)
    if task_id:
        find_task(data, task_id)
    path = pkg / "context" / f"{context_type}.jsonl"
    if context_type == "sources":
        if not all([source_id, source_type, location, title, why]):
            raise ArborError("sources context requires --source-id, --source-type, --location, --title, and --why.")
        if source_type not in SOURCE_TYPES:
            raise ArborError(f"Invalid source type '{source_type}'.")
        entry = {
            "id": source_id,
            "type": source_type,
            "location": location,
            "title": title,
            "why_it_matters": why,
        }
    else:
        if not summary:
            raise ArborError("impl/review context requires --summary.")
        if kind and kind not in CONTEXT_KINDS:
            raise ArborError(f"Invalid context kind '{kind}'.")
        entry = {
            "at": timestamp,
            "actor": actor,
            "task_id": task_id,
            "kind": kind or "note",
            "source": source,
            "summary": summary,
        }
    append_jsonl(path, entry)
    data["updated_at"] = timestamp
    save_package(pkg, data)
    return entry


def _validate_context_entry(context_type: str, entry: dict[str, Any]) -> None:
    if context_type not in CONTEXT_TYPES:
        raise ArborError(f"Invalid context type '{context_type}'.")
    if context_type == "sources":
        required = ["id", "type", "location", "title", "why_it_matters"]
        missing = [field for field in required if not entry.get(field)]
        if missing:
            raise ArborError("sources context entry missing required fields: " + ", ".join(missing))
        if entry.get("type") not in SOURCE_TYPES:
            raise ArborError(f"Invalid source type '{entry.get('type')}'.")
    else:
        if not entry.get("summary"):
            raise ArborError("impl/review context entry requires summary.")
        if entry.get("kind") is not None and entry.get("kind") not in CONTEXT_KINDS:
            raise ArborError(f"Invalid context kind '{entry.get('kind')}'.")


def add_context_batch(root: Path, name: str, context_type: str, entries: list[dict[str, Any]], actor: str, timestamp: str) -> dict[str, Any]:
    validate_name(name)
    if not entries:
        raise ArborError("At least one context entry is required.")
    pkg, data = load_package(root, name)
    for entry in entries:
        if not isinstance(entry, dict):
            raise ArborError("Context batch entries must be JSON objects.")
        task_id = entry.get("task_id")
        if task_id:
            find_task(data, task_id)
        _validate_context_entry(context_type, entry)
    path = pkg / "context" / f"{context_type}.jsonl"
    written: list[dict[str, Any]] = []
    for entry in entries:
        if context_type == "sources":
            normalized = {
                "id": entry["id"],
                "type": entry["type"],
                "location": entry["location"],
                "title": entry["title"],
                "why_it_matters": entry["why_it_matters"],
            }
        else:
            normalized = {
                "at": entry.get("at") or timestamp,
                "actor": entry.get("actor") or actor,
                "task_id": entry.get("task_id"),
                "kind": entry.get("kind") or "note",
                "source": entry.get("source"),
                "summary": entry["summary"],
            }
        append_jsonl(path, normalized)
        written.append(normalized)
    data["updated_at"] = timestamp
    save_package(pkg, data)
    return {"package": name, "type": context_type, "count": len(written), "entries": written}


def parse_entry_json(raw: str) -> dict[str, Any]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ArborError(f"Invalid entry JSON: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise ArborError("Entry JSON must be an object.")
    return value


def parse_entries_json(raw: str) -> list[dict[str, Any]]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ArborError(f"Invalid entries JSON: {exc.msg}") from exc
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise ArborError("Entries JSON must be an array of objects.")
    return value
