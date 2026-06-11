from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .errors import ArborError
from .fs import load_package, validate_name
from .slice_defs import slice_defs
from .state import ensure_execution
from .validation import validate_package


def _strip_line_locator(value: str) -> str:
    value = re.sub(r":(?:L)?\d+(?=\b|$)", "", value.strip())
    return re.sub(r"\s+", " ", value).strip(" `")


def _split_field_items(value: str) -> list[str]:
    items: list[str] = []
    for raw in re.split(r"[\n,，、;；]", value):
        item = _strip_line_locator(raw.lstrip("- ").strip())
        if item and item not in items:
            items.append(item)
    return items


def _slice_progress(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    entries = data.get("slices")
    if not isinstance(entries, list):
        return {}
    return {item.get("id"): item for item in entries if isinstance(item, dict) and isinstance(item.get("id"), str)}


def _acceptance_by_slice(impl_result: dict[str, Any]) -> dict[str, list[str]]:
    coverage = impl_result.get("acceptance_coverage")
    if isinstance(coverage, dict):
        return {key: value for key, value in coverage.items() if isinstance(key, str) and isinstance(value, list)}
    return {}


def module_summary(root: Path, package: str, timestamp: str | None = None) -> dict[str, Any]:
    validate_name(package)
    pkg, data = load_package(root, package)
    execution = ensure_execution(data)
    errors = validate_package(root, package)
    try:
        prd_slices = slice_defs(pkg, data, persist_migration=False)
        prd_errors: list[str] = []
    except ArborError as exc:
        prd_slices, prd_errors = [], [str(exc)]
    progress = _slice_progress(data)
    impl_result = data.get("impl_result") if isinstance(data.get("impl_result"), dict) else {}
    acceptance = _acceptance_by_slice(impl_result)
    slices = [
        {
            "id": item.id,
            "title": item.title,
            "status": progress.get(item.id, {}).get("status", "pending"),
            "completion_marker": item.completion_marker,
            "acceptance": acceptance.get(item.id, []),
        }
        for item in prd_slices
    ]
    contracts = [
        {
            "slice": item.id,
            "title": item.title,
            "completion_marker": item.completion_marker,
            "code_anchors": _split_field_items(item.code_anchors),
            "data_schema": _split_field_items(item.data_schema),
            "tests": _split_field_items(item.tests),
        }
        for item in prd_slices
    ]
    important_files: list[str] = []
    tests: list[str] = []
    for contract in contracts:
        for anchor in contract["code_anchors"]:
            if anchor and anchor not in important_files:
                important_files.append(anchor)
        for test in contract["tests"]:
            if test and test not in tests:
                tests.append(test)
    for command in impl_result.get("commands", []) if isinstance(impl_result.get("commands"), list) else []:
        if isinstance(command, str) and command not in tests:
            tests.append(command)
    check_ids = impl_result.get("checks", []) if isinstance(impl_result.get("checks"), list) else []
    for check in data.get("checks", []) if isinstance(data.get("checks"), list) else []:
        if not isinstance(check, dict) or check.get("id") not in check_ids:
            continue
        command = check.get("command")
        if isinstance(command, str) and command not in tests:
            tests.append(command)
    verification = [{"ok": not errors, "source": "validate_package", "errors": errors}]
    if prd_errors:
        verification.append({"ok": False, "source": "slice_defs", "errors": prd_errors})
    if impl_result:
        verification.append({"ok": True, "source": "impl_result", "state": impl_result.get("state"), "commands": impl_result.get("commands", []), "checks": impl_result.get("checks", [])})
    return {
        "kind": "module-summary",
        "schema_version": "sdd-module-summary-v1",
        "package": package,
        "title": data.get("title") or package,
        "status": data.get("state"),
        "execution_status": execution.get("status"),
        "package_kind": data.get("package_kind", "single"),
        "important_files": important_files,
        "invariants": [],
        "slices": slices,
        "contracts": contracts,
        "tests": tests,
        "implementation": {
            "summary": impl_result.get("summary"),
            "state": impl_result.get("state"),
            "acceptance": impl_result.get("acceptance", []),
            "commands": impl_result.get("commands", []),
            "checks": impl_result.get("checks", []),
            "check_coverage": impl_result.get("check_coverage", {}),
            "concerns": impl_result.get("concerns", []),
        },
        "verification": verification,
        "related_packages": [],
    }
