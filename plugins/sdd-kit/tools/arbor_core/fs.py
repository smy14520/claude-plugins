from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .errors import ArborError
from .schema import NAME_RE


def now_iso(override: str | None = None) -> str:
    if override:
        return override
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def arbor_root(root: Path) -> Path:
    return root / ".arbor"


def tasks_root(root: Path) -> Path:
    return arbor_root(root) / "tasks"


def package_dir(root: Path, name: str) -> Path:
    validate_name(name)
    return tasks_root(root) / name


def validate_name(name: str) -> None:
    if not NAME_RE.match(name):
        raise ArborError(f"Invalid package name '{name}'. Use kebab-case lowercase letters and digits.")


def read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ArborError(f"Missing JSON file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ArborError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ArborError(f"JSON root must be an object: {path}")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_if_missing(path: Path, content: str) -> bool:
    if path.exists():
        return False
    path.write_text(content, encoding="utf-8")
    return True


def append_jsonl(path: Path, entry: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False, separators=(",", ":")) + "\n")


def task_json_path(pkg: Path) -> Path:
    return pkg / "task.json"


def load_package(root: Path, name: str) -> tuple[Path, dict[str, Any]]:
    pkg = package_dir(root, name)
    return pkg, read_json(task_json_path(pkg))


def save_package(pkg: Path, data: dict[str, Any]) -> None:
    write_json(task_json_path(pkg), data)