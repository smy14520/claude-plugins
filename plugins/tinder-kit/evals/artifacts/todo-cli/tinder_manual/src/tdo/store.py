"""Storage layer: one JSON file, atomic writes, .bak rotation (ADR-0001)."""

from __future__ import annotations

import json
import os
from pathlib import Path

ENV_HOME = "TODO_HOME"
DEFAULT_DIR = Path("~/.todo")
FILE_NAME = "todo.json"
SCHEMA_VERSION = 1


class StoreError(Exception):
    """Storage-level failure (exit code 1)."""


def store_dir() -> Path:
    return Path(os.environ.get(ENV_HOME, str(DEFAULT_DIR))).expanduser()


def store_path() -> Path:
    return store_dir() / FILE_NAME


def bak_path(path: Path) -> Path:
    return path.with_name(path.name + ".bak")


def empty() -> dict:
    return {"version": SCHEMA_VERSION, "next_id": 1, "tasks": []}


def load(path: Path | None = None) -> dict:
    path = path or store_path()
    if not path.exists():
        return empty()
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise StoreError(f"cannot read store {path}: {exc}") from exc
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise StoreError(
            f"store {path} is corrupt ({exc}); restore from {bak_path(path)} or fix it by hand"
        ) from exc
    if not isinstance(data, dict) or not isinstance(data.get("tasks"), list):
        raise StoreError(f"store {path} has an unexpected shape; restore from {bak_path(path)}")
    version = data.get("version")
    if version != SCHEMA_VERSION:
        raise StoreError(f"store {path} has unsupported version {version!r}")
    next_id = data.get("next_id")
    if not isinstance(next_id, int) or next_id < 1:
        # hand-edited or pre-counter store: rederive the high-water mark
        data["next_id"] = max((task.get("id", 0) for task in data["tasks"]), default=0) + 1
    return data


def save(data: dict, path: Path | None = None) -> None:
    path = path or store_path()
    payload = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    try:
        tmp.write_text(payload, encoding="utf-8")
        if path.exists():
            os.replace(path, bak_path(path))  # keep one previous generation
        os.replace(tmp, path)
    except OSError as exc:
        raise StoreError(f"cannot write store {path}: {exc}") from exc
    finally:
        tmp.unlink(missing_ok=True)
