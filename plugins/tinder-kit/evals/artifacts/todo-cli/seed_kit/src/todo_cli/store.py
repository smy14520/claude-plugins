"""Storage layer: the single ``./.todos.json`` file.

Contract (``.arbor/.wiki/decision/single-json-storage-and-id-policy``):

- one file, cwd-relative, top level ``{"next_id": int, "todos": [record...]}``;
- ``next_id`` is a persisted monotonic counter, never ``max(id) + 1``;
- every write goes through ``<path>.tmp`` + :func:`os.replace` so the file on
  disk is always either the old or the new complete document;
- reads never create the file, and failed operations never touch it.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

FILE_NAME = ".todos.json"

#: Priority vocabulary, part of the on-disk schema and therefore owned here.
PRIORITIES = ("high", "med", "low")

#: Fixed record shape, frozen in S-001. Later slices add CLI flags, not fields.
RECORD_FIELDS = ("id", "title", "tags", "priority", "done", "created_at", "completed_at")


class StoreError(Exception):
    """The data file exists but does not match the documented schema."""


def data_path() -> Path:
    """Path of the data file, resolved against the current working directory."""
    return Path(FILE_NAME)


def empty_data() -> dict:
    """In-memory shape used when the file does not exist yet."""
    return {"next_id": 1, "todos": []}


def load() -> dict:
    """Read the data file, or return an empty document when it is absent.

    Never creates the file: only write operations touch the disk.
    """
    try:
        raw = data_path().read_text(encoding="utf-8")
    except FileNotFoundError:
        return empty_data()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise StoreError(f"{FILE_NAME} is not valid JSON: {exc}") from exc
    return validate(data)


def save(data: dict) -> None:
    """Write the whole document atomically: tmp file first, then replace."""
    target = data_path()
    tmp = target.with_name(target.name + ".tmp")
    payload = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    with open(tmp, "w", encoding="utf-8") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    try:
        os.replace(tmp, target)
    except BaseException:
        # Re-raise unchanged; just do not leave the temp file behind.
        tmp.unlink(missing_ok=True)
        raise


def validate(data: object) -> dict:
    """Check the document against the schema and return it unchanged.

    Deliberately tolerant of unknown extra keys inside a record (the file is a
    user-owned asset) but strict about the fields this tool relies on.
    """
    if not isinstance(data, dict):
        raise StoreError(f"{FILE_NAME}: top level must be an object")
    next_id = data.get("next_id")
    if not _is_int(next_id):
        raise StoreError(f"{FILE_NAME}: 'next_id' must be an integer")
    todos = data.get("todos")
    if not isinstance(todos, list):
        raise StoreError(f"{FILE_NAME}: 'todos' must be a list")
    for position, record in enumerate(todos):
        _validate_record(record, position)
    return data


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _validate_record(record: object, position: int) -> None:
    where = f"{FILE_NAME}: todos[{position}]"
    if not isinstance(record, dict):
        raise StoreError(f"{where} must be an object")
    for field in RECORD_FIELDS:
        if field not in record:
            raise StoreError(f"{where} is missing '{field}'")
    if not _is_int(record["id"]):
        raise StoreError(f"{where}: 'id' must be an integer")
    if not isinstance(record["title"], str) or not record["title"].strip():
        raise StoreError(f"{where}: 'title' must be a non-empty string")
    tags = record["tags"]
    if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
        raise StoreError(f"{where}: 'tags' must be a list of strings")
    if record["priority"] not in PRIORITIES:
        raise StoreError(f"{where}: 'priority' must be one of {', '.join(PRIORITIES)}")
    if not isinstance(record["done"], bool):
        raise StoreError(f"{where}: 'done' must be a boolean")
    if not isinstance(record["created_at"], str):
        raise StoreError(f"{where}: 'created_at' must be a string")
    completed_at = record["completed_at"]
    # Sorting reads completed_at on every done record, so the invariant is
    # enforced in both directions: done <=> completed_at is a timestamp string.
    if record["done"] and not isinstance(completed_at, str):
        raise StoreError(f"{where}: 'completed_at' must be a string when done is true")
    if not record["done"] and completed_at is not None:
        raise StoreError(f"{where}: 'completed_at' must be null when done is false")
