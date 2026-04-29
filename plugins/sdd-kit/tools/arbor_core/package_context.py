from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import ArborError
from .fs import *
from .schema import *
from .package_lifecycle import find_task


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
