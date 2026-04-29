from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import ArborError
from .fs import *


DEFAULT_IMPORT_ARTIFACTS = [
    "prd.md",
    "task.md",
    "review.md",
    "context/impl.jsonl",
    "context/review.jsonl",
    "context/sources.jsonl",
]


ARTIFACT_ALIASES = {
    "prd": "prd.md",
    "task": "task.md",
    "review": "review.md",
    "impl": "context/impl.jsonl",
    "context/impl": "context/impl.jsonl",
    "review-context": "context/review.jsonl",
    "context/review": "context/review.jsonl",
    "source": "context/sources.jsonl",
    "sources": "context/sources.jsonl",
    "context/sources": "context/sources.jsonl",
}


def safe_artifact_ref(path: str) -> str:
    value = ARTIFACT_ALIASES.get(path.strip().replace("\\", "/"), path.strip().replace("\\", "/"))
    if not value or value.startswith("/") or value.startswith("../") or "/../" in value or value == "task.json":
        raise ArborError(f"Invalid package artifact path '{path}'.")
    if value.startswith("context/"):
        if value.count("/") != 1:
            raise ArborError(f"Invalid context artifact path '{path}'.")
        suffix = value.rsplit(".", 1)[-1]
        if suffix not in {"jsonl", "md"}:
            raise ArborError(f"Unsupported context artifact type '{path}'.")
        return value
    if value not in {"prd.md", "task.md", "review.md"}:
        raise ArborError(f"Unsupported package artifact '{path}'.")
    return value


def resolve_package_artifact_source(root: Path, from_worktree: str) -> Path:
    if not from_worktree.strip():
        raise ArborError("--from-worktree is required.")
    raw = Path(from_worktree.strip())
    return raw.resolve() if raw.is_absolute() else (root / raw).resolve()


def import_package_artifacts(root: Path, name: str, from_worktree: str, artifacts: list[str] | None, actor: str, timestamp: str) -> dict[str, Any]:
    validate_name(name)
    source_root = resolve_package_artifact_source(root, from_worktree)
    if not source_root.exists():
        raise ArborError(f"Source worktree does not exist: {source_root}")
    source_pkg = package_dir(source_root, name)
    target_pkg = package_dir(root, name)
    if not source_pkg.exists():
        raise ArborError(f"Source package artifact directory does not exist: {source_pkg}")
    if not target_pkg.exists():
        raise ArborError(f"Target package does not exist: {target_pkg}")

    requested = artifacts if artifacts else DEFAULT_IMPORT_ARTIFACTS
    normalized: list[str] = []
    for artifact in requested:
        ref = safe_artifact_ref(artifact)
        if ref not in normalized:
            normalized.append(ref)

    imported: list[str] = []
    missing: list[str] = []
    for ref in normalized:
        source = source_pkg / ref
        target = target_pkg / ref
        if not source.exists():
            missing.append(ref)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        content = source.read_bytes()
        changed = not target.exists() or target.read_bytes() != content
        if changed:
            target.write_bytes(content)
            imported.append(ref)

    data = read_json(task_json_path(target_pkg))
    data.setdefault("artifact_imports", []).append(
        {
            "at": timestamp,
            "actor": actor,
            "from_worktree": from_worktree.strip(),
            "resolved_from_worktree": str(source_root),
            "imported": imported,
            "checked": normalized,
            "missing": missing,
            "excluded_control_state": ["task.json"],
        }
    )
    data["updated_at"] = timestamp
    save_package(target_pkg, data)
    return {"package": name, "from_worktree": from_worktree.strip(), "imported": imported, "checked": normalized, "missing": missing, "excluded_control_state": ["task.json"]}
