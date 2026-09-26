"""Core semantics: task records, lifecycle transitions, filtering and ordering.

Functions here work on the in-memory document produced by :mod:`todo_cli.store`
and mutate it in place. They raise :class:`TodoError` for every user-facing
domain problem (unknown id, forbidden transition, blank title) so the caller can
decide about exit codes and stderr, and they never write to disk themselves.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime

from .store import PRIORITIES

#: Sort rank for priorities: lower sorts first (high > med > low).
PRIORITY_RANK = {priority: rank for rank, priority in enumerate(PRIORITIES)}

#: State space: pending (done=false) and done (done=true), nothing else.
PENDING = False
DONE = True


class TodoError(Exception):
    """A domain-level rejection: bad id, forbidden transition, or blank title."""


def utc_now_iso() -> str:
    """Current UTC time as ``YYYY-MM-DDTHH:MM:SSZ``."""
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def dedupe_tags(tags: Iterable[str]) -> list[str]:
    """Drop duplicate tags while keeping first-seen order."""
    seen: dict[str, None] = {}
    for tag in tags:
        seen.setdefault(tag, None)
    return list(seen)


def allocate_id(data: dict) -> int:
    """Return the next id to hand out without consuming it.

    ``next_id`` is the source of truth. ``max(..., max(id) + 1)`` only guards
    against a hand-edited file whose counter lags the records in it: it can
    bump the counter upward but never reuses or rewinds it.
    """
    highest = max((record["id"] for record in data["todos"]), default=0)
    return max(data["next_id"], highest + 1)


def index_of(data: dict, todo_id: int) -> int:
    for position, record in enumerate(data["todos"]):
        if record["id"] == todo_id:
            return position
    raise TodoError(f"no todo with id #{todo_id}")


def add_todo(data: dict, *, title: str, tags: list[str], priority: str) -> dict:
    """Append a pending record and consume one step of ``next_id``.

    Returns the new record; its ``id`` is the one just handed out.
    """
    _check_title(title)
    todo_id = allocate_id(data)
    data["todos"].append(
        {
            "id": todo_id,
            "title": title,
            "tags": dedupe_tags(tags),
            "priority": priority,
            "done": PENDING,
            "created_at": utc_now_iso(),
            "completed_at": None,
        }
    )
    data["next_id"] = todo_id + 1
    return data["todos"][-1]


def mark_done(data: dict, todo_id: int) -> dict:
    record = data["todos"][index_of(data, todo_id)]
    if record["done"]:
        raise TodoError(f"#{todo_id} is already done")
    record["done"] = DONE
    record["completed_at"] = utc_now_iso()
    return record


def reopen(data: dict, todo_id: int) -> dict:
    record = data["todos"][index_of(data, todo_id)]
    if not record["done"]:
        raise TodoError(f"#{todo_id} is not done")
    record["done"] = PENDING
    record["completed_at"] = None
    return record


def remove(data: dict, todo_id: int) -> dict:
    """Drop a single record; ``next_id`` is left untouched so ids never recycle."""
    position = index_of(data, todo_id)
    return data["todos"].pop(position)


def clear_done(data: dict) -> list[dict]:
    """Remove every done record, keep pending ones in order, keep ``next_id``.

    Returns the removed records; an empty list means there was nothing to do and
    the caller must not save.
    """
    removed = [record for record in data["todos"] if record["done"]]
    if removed:
        data["todos"] = [record for record in data["todos"] if not record["done"]]
    return removed


def edit_todo(
    data: dict,
    todo_id: int,
    *,
    title: str | None = None,
    tags: list[str] | None = None,
    priority: str | None = None,
) -> tuple[dict, bool]:
    """Update only the fields the caller passed; completion state never changes.

    ``tags`` uses whole-replacement semantics (``None`` means "not given").
    Returns the record and whether anything actually changed.
    """
    record = data["todos"][index_of(data, todo_id)]
    changed = False
    if title is not None:
        _check_title(title)
        record["title"] = title
        changed = True
    if priority is not None:
        if priority not in PRIORITIES:
            raise TodoError(f"priority must be one of {', '.join(PRIORITIES)}")
        record["priority"] = priority
        changed = True
    if tags is not None:
        record["tags"] = dedupe_tags(tags)
        changed = True
    return record, changed


def matches(
    record: dict,
    *,
    tags: list[str] | tuple[str, ...] = (),
    priority: str | None = None,
    include_done: bool = False,
) -> bool:
    """Filter predicate: default "pending only", plus tag AND and priority."""
    if not include_done and record["done"]:
        return False
    if priority is not None and record["priority"] != priority:
        return False
    if tags:
        owned = set(record["tags"])
        if not all(tag in owned for tag in tags):
            return False
    return True


def order(records: list[dict]) -> list[dict]:
    """The one sort rule every view shares.

    Pending first: priority (high > med > low), ties by id ascending. Done
    records come after all pending ones, newest completion first, ties (same
    second) by id descending. Timestamps sort lexicographically because they are
    all UTC ISO 8601 of the same shape.
    """
    pending = sorted(
        (record for record in records if not record["done"]),
        key=lambda record: (PRIORITY_RANK[record["priority"]], record["id"]),
    )
    done = sorted(
        (record for record in records if record["done"]),
        key=lambda record: (record["completed_at"], record["id"]),
        reverse=True,
    )
    return pending + done


def select(
    data: dict,
    *,
    tags: list[str] | tuple[str, ...] = (),
    priority: str | None = None,
    include_done: bool = False,
) -> list[dict]:
    """Filter then order; the only query path, shared by text and JSON views."""
    selected = [
        record
        for record in data["todos"]
        if matches(record, tags=tags, priority=priority, include_done=include_done)
    ]
    return order(selected)


def _check_title(title: str) -> None:
    if not title.strip():
        raise TodoError("title must not be empty")
