from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .errors import ArborError
from .fs import package_dir, validate_name
from .package_lifecycle import set_package_sizing, update_prd_status
from .package_model import create_package
from .validation import validate_package

_LEGACY_SLICE_CHECKBOX_RE = re.compile(r"^- \[[ x\-]\] S-\d{3}", re.MULTILINE)
_SLICE_SECTION_RE = re.compile(r"^## Slices\b.*?(?=^## |\Z)", re.MULTILINE | re.DOTALL)
_SLICE_BLOCK_RE = re.compile(
    r"^### (S-\d{3}):.*?(?=^### S-\d{3}:|^## |\Z)",
    re.MULTILINE | re.DOTALL,
)
_SLICE_SCAFFOLD_TOKENS = (
    "<walking skeleton 或第一个独立可验证的契约/功能>",
    "<扩展某个契约/功能/行为/状态转换>",
    "<回归 / 边界 / 自检切片>",
    "<完成后多了什么可独立验证的契约/功能/行为>",
    "Impl 只更新 [ ] / [-] / [x]",
)


def _validate_prd_slice_structure(prd_text: str) -> None:
    """Enforce the structured `## Slices` contract before finalize writes the PRD.

    A PRD is ready only if its `## Slices` section contains at least one
    `### S-NNN:` slice header, **each** slice block carries its own
    `完成标志` marker, the PRD uses no legacy `- [ ] S-NNN` checkbox format,
    and contains no unfilled template scaffold tokens.
    """
    errors: list[str] = []
    if "## Slices" not in prd_text:
        errors.append("missing `## Slices` section")
        raise ArborError(
            "finalize-brainstorm PRD structure invalid: " + "; ".join(errors)
        )

    slice_section_match = _SLICE_SECTION_RE.search(prd_text)
    slice_section = slice_section_match.group(0) if slice_section_match else ""

    slice_blocks = list(_SLICE_BLOCK_RE.finditer(slice_section))
    if not slice_blocks:
        errors.append(
            "`## Slices` must contain at least one `### S-NNN:` slice header"
        )
    else:
        missing_markers = [
            match.group(1)
            for match in slice_blocks
            if "完成标志" not in match.group(0)
        ]
        if missing_markers:
            errors.append(
                "slices missing `完成标志` marker: " + ", ".join(missing_markers)
            )

    if _LEGACY_SLICE_CHECKBOX_RE.search(prd_text):
        errors.append(
            "PRD uses legacy `- [ ] S-NNN` checkbox format; migrate to `### S-NNN:` structured slices"
        )
    scaffold_hits = [tok for tok in _SLICE_SCAFFOLD_TOKENS if tok in prd_text]
    if scaffold_hits:
        errors.append(
            "PRD contains unfilled slice scaffold tokens: " + ", ".join(scaffold_hits)
        )

    if errors:
        raise ArborError(
            "finalize-brainstorm PRD structure invalid: " + "; ".join(errors)
        )


def _required_string(data: dict[str, Any], field: str) -> str:
    value = data.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ArborError(f"finalize-brainstorm requires non-empty {field}.")
    return value.strip()


def _required_string_any(data: dict[str, Any], fields: tuple[str, ...], label: str) -> str:
    for field in fields:
        value = data.get(field)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if value is not None and not isinstance(value, str):
            raise ArborError(f"{field} must be a string when provided.")
    raise ArborError(f"finalize-brainstorm requires non-empty {label}.")


def _optional_string(data: dict[str, Any], field: str) -> str | None:
    value = data.get(field)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ArborError(f"{field} must be a string when provided.")
    value = value.strip()
    return value or None


def _write_prd(root: Path, name: str, prd: str | None) -> None:
    if prd is None:
        return
    text = prd.rstrip() + "\n"
    (package_dir(root, name) / "prd.md").write_text(text, encoding="utf-8")


def _read_prd_path(root: Path, path_value: str | None) -> str | None:
    if not path_value:
        return None
    path = Path(path_value)
    if not path.is_absolute():
        path = root / path
    try:
        resolved = path.resolve()
        root_resolved = root.resolve()
        resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise ArborError("prd_path must stay inside project root.") from exc
    if not resolved.exists():
        raise ArborError(f"prd_path does not exist: {path_value}")
    if not resolved.is_file():
        raise ArborError(f"prd_path must point to a file: {path_value}")
    return resolved.read_text(encoding="utf-8")


def _package_summary(root: Path, name: str) -> dict[str, Any]:
    errors = validate_package(root, name)
    task_json = package_dir(root, name) / "task.json"
    data = json.loads(task_json.read_text(encoding="utf-8")) if task_json.exists() else {}
    return {
        "name": name,
        "path": f".arbor/tasks/{name}",
        "state": data.get("state"),
        "next_action": data.get("next_action"),
        "validation": {"ok": not errors, "errors": errors},
    }


def _validate_created(root: Path, names: list[str]) -> None:
    all_errors: dict[str, list[str]] = {}
    for name in names:
        errors = validate_package(root, name)
        if errors:
            all_errors[name] = errors
    if all_errors:
        rendered = "; ".join(f"{name}: {', '.join(errors)}" for name, errors in all_errors.items())
        raise ArborError(f"finalize-brainstorm produced invalid package state: {rendered}")


def finalize_brainstorm(root: Path, spec: dict[str, Any], timestamp: str) -> dict[str, Any]:
    """Finalize a brainstorm PRD into a single ready package.

    All packages are single. Large scopes use PRD-local Slices instead of
    materialized package splitting.
    """
    if not isinstance(spec, dict):
        raise ArborError("finalize-brainstorm input must be a JSON object.")

    # Accept but ignore legacy kind fields; finalize always creates one package.
    kind = spec.get("kind") or spec.get("package_kind") or "single"
    if kind != "single":
        raise ArborError("finalize-brainstorm only supports single packages; use PRD ## Slices for large scopes.")

    name = _required_string_any(spec, ("name", "package"), "name or package")
    validate_name(name)
    title = _optional_string(spec, "title") or name
    if "mode" in spec:
        raise ArborError("finalize-brainstorm no longer accepts mode; PRD-first packages have a single execution path.")
    prd = _optional_string(spec, "prd") or _read_prd_path(root, _optional_string(spec, "prd_path"))
    if not prd or not prd.strip():
        raise ArborError("finalize-brainstorm requires non-empty prd or prd_path.")
    _validate_prd_slice_structure(prd)
    decision = _optional_string(spec, "decision")

    create_package(root, name, title, "new", timestamp)
    _write_prd(root, name, prd)
    set_package_sizing(root, name, "fits_package", "brainstorm", "brainstorm finalized package", timestamp, decision or "single package with PRD-local Slices", [], [], "brainstorm")
    update_prd_status(root, name, "ready", "brainstorm", "brainstorm finalized PRD", timestamp)
    _validate_created(root, [name])
    summary = _package_summary(root, name)
    return {"kind": "single", "root_package": name, "packages": [summary]}
