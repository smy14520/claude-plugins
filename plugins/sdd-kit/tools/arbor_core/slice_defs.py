from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import ArborError
from .fs import save_package
from .prd_slices import PrdSlice, parse_prd_slices


def _serialize(item: PrdSlice) -> dict[str, Any]:
    return {
        "id": item.id,
        "title": item.title,
        "completion_markers": list(item.completion_markers),
        "code_anchors": item.code_anchors,
        "data_schema": item.data_schema,
        "tests": item.tests,
    }


def _deserialize(entry: dict[str, Any]) -> PrdSlice:
    markers = entry.get("completion_markers")
    return PrdSlice(
        id=str(entry.get("id", "")),
        title=str(entry.get("title", "")),
        body="",
        completion_markers=tuple(str(item) for item in markers) if isinstance(markers, list) else (),
        code_anchors=str(entry.get("code_anchors", "")),
        data_schema=str(entry.get("data_schema", "")),
        tests=str(entry.get("tests", "")),
    )


def materialize_slice_defs(pkg: Path, data: dict[str, Any]) -> list[PrdSlice]:
    """Compile PRD `## Slices` into task.json `prd.slices`.

    This is the parse-once boundary: prd.md is prose for humans and models;
    runtime commands consume the materialized snapshot instead of re-parsing
    markdown. Called at finalize and on every entry into `doing` (where the
    PRD freezes), so the snapshot cannot go stale mid-execution.
    """
    prd_path = pkg / "prd.md"
    if not prd_path.exists():
        raise ArborError(f"Missing PRD file: {prd_path}")
    slices, errors = parse_prd_slices(prd_path.read_text(encoding="utf-8"))
    if errors:
        raise ArborError("Cannot materialize PRD slices: " + "; ".join(errors))
    prd = data.setdefault("prd", {})
    if not isinstance(prd, dict):
        raise ArborError("task.json prd must be an object.")
    prd["slices"] = [_serialize(item) for item in slices]
    return slices


def slice_defs(pkg: Path, data: dict[str, Any], persist_migration: bool = True) -> list[PrdSlice]:
    """Return materialized slice definitions.

    Legacy packages without `prd.slices` are lazily migrated by parsing
    prd.md once and persisting the snapshot (unless persist_migration=False,
    for read-only callers like validation).
    """
    prd = data.get("prd") if isinstance(data.get("prd"), dict) else {}
    entries = prd.get("slices")
    if isinstance(entries, list) and entries:
        return [_deserialize(entry) for entry in entries if isinstance(entry, dict)]
    slices = materialize_slice_defs(pkg, data)
    if persist_migration:
        save_package(pkg, data)
    return slices
