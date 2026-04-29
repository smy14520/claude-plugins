from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import ArborError
from .fs import *
from .schema import *
from .map_model import ensure_map_workspace


def append_parallel_runtime_event(
    root: Path,
    initiative: str,
    event: str,
    actor: str,
    timestamp: str,
    package: str | None = None,
    assignment_id: str | None = None,
    worker: str | None = None,
    reason: str | None = None,
    detail: dict[str, Any] | None = None,
) -> dict[str, Any]:
    validate_name(initiative)
    if package is not None:
        validate_name(package)
    if event not in PARALLEL_RUNTIME_EVENTS:
        raise ArborError(f"Invalid parallel runtime event '{event}'.")
    if not actor.strip():
        raise ArborError("Parallel runtime event actor is required.")
    if assignment_id is not None and not assignment_id.strip():
        raise ArborError("Parallel runtime event assignment_id cannot be empty.")
    if worker is not None and not worker.strip():
        raise ArborError("Parallel runtime event worker cannot be empty.")
    if reason is not None and not reason.strip():
        raise ArborError("Parallel runtime event reason cannot be empty.")
    if detail is not None and not isinstance(detail, dict):
        raise ArborError("Parallel runtime event detail must be a JSON object.")

    ensure_map_workspace(root, initiative, timestamp)
    record: dict[str, Any] = {
        "at": timestamp,
        "kind": "runtime_event",
        "event": event,
        "initiative": initiative,
        "actor": actor,
    }
    if package is not None:
        record["package"] = package
    if assignment_id is not None:
        record["assignment_id"] = assignment_id.strip()
    if worker is not None:
        record["worker"] = worker.strip()
    if reason is not None:
        record["reason"] = reason.strip()
    if detail is not None:
        record["detail"] = detail
    append_jsonl(map_context_dir(root, initiative) / "agent-assignments.jsonl", record)
    return record
