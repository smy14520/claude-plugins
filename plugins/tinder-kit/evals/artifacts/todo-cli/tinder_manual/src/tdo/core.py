"""Domain logic: task operations and tag filtering (pure, no I/O)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

PENDING = "pending"
DONE = "done"


class ValidationError(Exception):
    """Bad user input (exit code 2)."""


class NotFound(Exception):
    """No task with the given id (exit code 1)."""

    def __init__(self, task_id: int) -> None:
        super().__init__(f"no task with id {task_id}")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def normalize_tags(raw: Iterable[str]) -> list[str]:
    """Lowercase, trim, split on commas, drop empties, dedupe, sort."""
    tags: set[str] = set()
    for item in raw:
        for piece in str(item).split(","):
            piece = piece.strip().lower()
            if piece:
                tags.add(piece)
    return sorted(tags)


def parse_tag_groups(flags: list[str]) -> list[list[str]]:
    """Each --tag occurrence becomes one OR-group; groups combine with AND."""
    groups = [normalize_tags([flag]) for flag in flags]
    if any(not group for group in groups):
        raise ValidationError("--tag value contains no usable tag")
    return groups


def take_next_id(data: dict) -> int:
    """Read and advance the persisted high-water mark so ids are never reused.

    `data` must come from store.load(), which guarantees a valid `next_id`.
    """
    task_id = data["next_id"]
    data["next_id"] = task_id + 1
    return task_id


def add(tasks: list[dict], title: str, tags: Iterable[str], task_id: int) -> dict:
    title = title.strip()
    if not title:
        raise ValidationError("task title cannot be empty")
    task = {
        "id": task_id,
        "title": title,
        "tags": normalize_tags(tags),
        "status": PENDING,
        "created_at": now_iso(),
        "completed_at": None,
    }
    tasks.append(task)
    return task


def find(tasks: list[dict], task_id: int) -> dict:
    for task in tasks:
        if task["id"] == task_id:
            return task
    raise NotFound(task_id)


def done(tasks: list[dict], task_id: int) -> tuple[dict, bool]:
    """Mark done; idempotent. Returns (task, changed)."""
    task = find(tasks, task_id)
    if task["status"] == DONE:
        return task, False
    task["status"] = DONE
    task["completed_at"] = now_iso()
    return task, True


def reopen(tasks: list[dict], task_id: int) -> tuple[dict, bool]:
    """Back to pending; idempotent. Returns (task, changed)."""
    task = find(tasks, task_id)
    if task["status"] == PENDING:
        return task, False
    task["status"] = PENDING
    task["completed_at"] = None
    return task, True


def remove(tasks: list[dict], task_id: int) -> dict:
    task = find(tasks, task_id)
    tasks.remove(task)
    return task


def used_tags(tasks: list[dict]) -> set[str]:
    return {tag for task in tasks for tag in task["tags"]}


def filter_tasks(
    tasks: list[dict], groups: list[list[str]], include_done: bool = False
) -> tuple[list[dict], list[str]]:
    """AND across groups, OR within a group. Returns (matches, unknown_groups)."""
    used = used_tags(tasks)
    unknown = ["|".join(group) for group in groups if not set(group) & used]
    matched = [
        task
        for task in tasks
        if (include_done or task["status"] == PENDING)
        and all(any(tag in task["tags"] for tag in group) for group in groups)
    ]
    matched.sort(key=lambda task: task["id"])
    return matched, unknown


def tag_counts(tasks: list[dict]) -> list[dict]:
    counts: dict[str, int] = {}
    for task in tasks:
        for tag in task["tags"]:
            counts[tag] = counts.get(tag, 0) + 1
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [{"tag": tag, "count": count} for tag, count in ranked]
