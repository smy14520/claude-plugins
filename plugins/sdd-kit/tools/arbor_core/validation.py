from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .errors import ArborError
from .fs import legacy_parent_map_ref, package_dir, parent_map_ref, read_json
from .schema import *


def parse_jsonl(path: Path, errors: list[str], required: set[str] | None = None) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    if not path.exists():
        errors.append(f"Missing file: {path}")
        return entries
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            entry = json.loads(raw)
        except json.JSONDecodeError as exc:
            errors.append(f"Invalid JSONL at {path}:{line_no}: {exc}")
            continue
        if not isinstance(entry, dict):
            errors.append(f"JSONL entry must be an object at {path}:{line_no}")
            continue
        missing = required - entry.keys() if required else set()
        if missing:
            errors.append(f"Missing JSONL fields at {path}:{line_no}: {', '.join(sorted(missing))}")
        entries.append(entry)
    return entries


def has_template_placeholders(path: Path) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    placeholder_patterns = [
        r"<[^>\n]*(?:feature|package|initiative|deliverable|path|behavior|里程碑|任务|hours|title|source|why|domain|contract|blocker|next)[^>\n]*>",
        r"\bSlice [A-Z]:\s*$",
    ]
    return any(re.search(pattern, text, re.MULTILINE) for pattern in placeholder_patterns)


def parse_markdown_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text
    meta: dict[str, str] = {}
    for raw in text[4:end].strip().splitlines():
        if not raw.strip() or raw.lstrip().startswith("#") or ":" not in raw:
            continue
        key, value = raw.split(":", 1)
        meta[key.strip()] = value.strip().strip('"\'')
    return meta, text[end + 4 :].lstrip("\n")


def validate_task_markdown(path: Path, data: dict[str, Any], task_ids: set[str], errors: list[str]) -> None:
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    meta, body = parse_markdown_frontmatter(text)
    if "[[" in body and re.search(r"\[\[[^\]]+\]\]", body):
        errors.append("task.md must be self-contained and must not contain wikilinks")
    name = data.get("name")
    if "package" in meta and meta.get("package") != name:
        errors.append(f"task.md frontmatter package '{meta.get('package')}' does not match task.json name '{name}'")
    mode = data.get("mode")
    if "mode" in meta and meta.get("mode") != mode:
        errors.append(f"task.md frontmatter mode '{meta.get('mode')}' does not match task.json mode '{mode}'")
    for task_id in sorted(task_ids):
        if task_id not in body:
            errors.append(f"task.md does not mention task id: {task_id}")


def validate_optional_string(value: Any, label: str, errors: list[str]) -> None:
    if value is not None and not isinstance(value, str):
        errors.append(f"{label} must be a string or null")


def validate_string_array(value: Any, label: str, errors: list[str]) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        errors.append(f"{label} must be a string array")
        return []
    return value


def validate_prd_amendments(prd: dict[str, Any], errors: list[str]) -> set[str]:
    amendments = prd.get("amendments", [])
    if amendments is None:
        return set()
    if not isinstance(amendments, list):
        errors.append("prd.amendments must be an array")
        return set()

    amendment_ids: set[str] = set()
    for index, amendment in enumerate(amendments):
        label = f"prd.amendments[{index}]"
        if not isinstance(amendment, dict):
            errors.append(f"{label} must be an object")
            continue
        for field in ["id", "title", "wrong", "correct", "created_at", "created_by"]:
            value = amendment.get(field)
            if not isinstance(value, str) or not value:
                errors.append(f"{label}.{field} must be a non-empty string")
        amendment_id = amendment.get("id")
        if isinstance(amendment_id, str):
            if not AMENDMENT_ID_RE.match(amendment_id):
                errors.append(f"Invalid amendment id: {amendment_id}")
            elif amendment_id in amendment_ids:
                errors.append(f"Duplicate amendment id: {amendment_id}")
            else:
                amendment_ids.add(amendment_id)
        if "source" in amendment:
            validate_optional_string(amendment.get("source"), f"{label}.source", errors)
        if "affects_tasks" in amendment:
            validate_string_array(amendment.get("affects_tasks"), f"{label}.affects_tasks", errors)
    return amendment_ids


def validate_parent_map_pair(parent_map: Any, parent_initiative: Any, label: str, errors: list[str]) -> None:
    if parent_map is None and parent_initiative is None:
        return
    if not isinstance(parent_map, str) or not isinstance(parent_initiative, str):
        errors.append(f"{label}.parent_map and {label}.parent_initiative must be strings when either is set")
        return
    if not NAME_RE.match(parent_initiative):
        errors.append(f"{label}.parent_initiative must be kebab-case")
        return
    expected = parent_map_ref(parent_initiative)
    legacy = legacy_parent_map_ref(parent_initiative)
    if parent_map not in {expected, legacy}:
        errors.append(f"{label}.parent_map must be {expected}")


def validate_package_sizing(data: dict[str, Any], errors: list[str]) -> None:
    sizing = data.get("package_sizing")
    if sizing is None:
        return
    if not isinstance(sizing, dict):
        errors.append("package_sizing must be an object")
        return
    status = sizing.get("status")
    if status not in PACKAGE_SIZING_STATUSES:
        errors.append(f"Invalid package_sizing.status: {status}")
    if status in {"fits_package", "split_applied"} and not sizing.get("decision"):
        errors.append(f"package_sizing.status {status} requires a non-empty decision")
    validate_optional_string(sizing.get("decision"), "package_sizing.decision", errors)
    validate_optional_string(sizing.get("decided_at"), "package_sizing.decided_at", errors)
    validate_optional_string(sizing.get("decided_by"), "package_sizing.decided_by", errors)
    validate_optional_string(sizing.get("note"), "package_sizing.note", errors)
    signals = sizing.get("signals", [])
    if not isinstance(signals, list) or not all(isinstance(item, str) for item in signals):
        errors.append("package_sizing.signals must be a string array")
    recommended = sizing.get("recommended_packages", [])
    if not isinstance(recommended, list):
        errors.append("package_sizing.recommended_packages must be an array")
    else:
        if status == "split_recommended" and not recommended:
            errors.append("package_sizing.status split_recommended requires at least one recommended package")
        for index, item in enumerate(recommended):
            if not isinstance(item, dict):
                errors.append(f"package_sizing.recommended_packages[{index}] must be an object")
                continue
            for field in ["name", "reason", "depends_on"]:
                if field not in item:
                    errors.append(f"package_sizing.recommended_packages[{index}] missing field: {field}")
            package_name = item.get("name")
            if not isinstance(package_name, str) or not NAME_RE.match(package_name):
                errors.append(f"package_sizing.recommended_packages[{index}].name must be kebab-case")
            validate_optional_string(item.get("reason"), f"package_sizing.recommended_packages[{index}].reason", errors)
            depends_on = item.get("depends_on", [])
            if not isinstance(depends_on, list) or not all(isinstance(dep, str) for dep in depends_on):
                errors.append(f"package_sizing.recommended_packages[{index}].depends_on must be a string array")
    validate_parent_map_pair(sizing.get("parent_map"), sizing.get("parent_initiative"), "package_sizing", errors)
    depends_on_packages = sizing.get("depends_on_packages", [])
    if not isinstance(depends_on_packages, list) or not all(isinstance(dep, str) for dep in depends_on_packages):
        errors.append("package_sizing.depends_on_packages must be a string array")
    else:
        package_name = data.get("name")
        for dep in depends_on_packages:
            if not NAME_RE.match(dep):
                errors.append(f"package_sizing.depends_on_packages entry must be kebab-case: {dep}")
            if dep == package_name:
                errors.append("package_sizing.depends_on_packages must not include self")
    validate_optional_string(sizing.get("boundary_reason"), "package_sizing.boundary_reason", errors)


def validate_execution(data: dict[str, Any], errors: list[str]) -> None:
    execution = data.get("execution")
    if execution is None:
        return
    if not isinstance(execution, dict):
        errors.append("execution must be an object")
        return
    name = data.get("name")
    if execution.get("boundary") != "package":
        errors.append("execution.boundary must be package")
    expected_path = f".arbor/tasks/{name}" if isinstance(name, str) else None
    if execution.get("unit_path") != expected_path:
        errors.append(f"execution.unit_path must be {expected_path}")
    if execution.get("child_task_scope") != "control_acceptance_review":
        errors.append("execution.child_task_scope must be control_acceptance_review")
    if execution.get("status") not in EXECUTION_STATUSES:
        errors.append(f"Invalid execution.status: {execution.get('status')}")
    for field in ["owner", "claimed_at", "released_at", "session", "updated_at", "updated_by", "note"]:
        validate_optional_string(execution.get(field), f"execution.{field}", errors)

    branch = execution.get("branch")
    if not isinstance(branch, dict):
        errors.append("execution.branch must be an object")
    else:
        for field in ["base", "name", "upstream"]:
            validate_optional_string(branch.get(field), f"execution.branch.{field}", errors)

    worktree = execution.get("worktree")
    if not isinstance(worktree, dict):
        errors.append("execution.worktree must be an object")
    else:
        for field in ["path", "created_by"]:
            validate_optional_string(worktree.get(field), f"execution.worktree.{field}", errors)

    pr = execution.get("pr")
    if not isinstance(pr, dict):
        errors.append("execution.pr must be an object")
    else:
        validate_optional_string(pr.get("url"), "execution.pr.url", errors)
        number = pr.get("number")
        if number is not None and not isinstance(number, int):
            errors.append("execution.pr.number must be an integer or null")
        if pr.get("state") not in PR_STATES:
            errors.append(f"Invalid execution.pr.state: {pr.get('state')}")

    if "agents" in execution and not isinstance(execution.get("agents"), list):
        errors.append("execution.agents must be an array when present")
    if "checkpoints" in execution and not isinstance(execution.get("checkpoints"), list):
        errors.append("execution.checkpoints must be an array when present")


def validate_package(root: Path, name: str) -> list[str]:
    pkg = package_dir(root, name)
    errors: list[str] = []
    required_files = [
        "prd.md",
        "task.md",
        "task.json",
        "review.md",
        "context/impl.jsonl",
        "context/review.jsonl",
        "context/sources.jsonl",
    ]
    for rel in required_files:
        if not (pkg / rel).exists():
            errors.append(f"Missing file: {pkg / rel}")

    if not (pkg / "task.json").exists():
        return errors

    try:
        data = read_json(pkg / "task.json")
    except ArborError as exc:
        return errors + [str(exc)]

    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"Unsupported schema_version: {data.get('schema_version')}")
    if data.get("name") != name:
        errors.append(f"task.json name '{data.get('name')}' does not match directory '{name}'")
    if data.get("mode") not in MODES:
        errors.append(f"Invalid mode: {data.get('mode')}")
    if data.get("state") not in TOP_LEVEL_STATES:
        errors.append(f"Invalid top-level state: {data.get('state')}")
    if data.get("current_phase") not in PHASES:
        errors.append(f"Invalid current_phase: {data.get('current_phase')}")
    next_action = data.get("next_action")
    if not isinstance(next_action, dict):
        errors.append("next_action must be an object")
    elif next_action.get("skill") not in NEXT_ACTION_SKILLS:
        errors.append(f"Invalid next_action.skill: {next_action.get('skill')}")

    amendment_ids: set[str] = set()
    pending_amendment_task_refs: list[tuple[str, str, str]] = []
    prd = data.get("prd")
    if not isinstance(prd, dict):
        errors.append("prd must be an object")
    else:
        amendment_ids = validate_prd_amendments(prd, errors)
        if prd.get("file") != "prd.md":
            errors.append("prd.file must be prd.md")
        if prd.get("status") not in {"draft", "ready-for-task", "revising", "superseded"}:
            errors.append(f"Invalid prd.status: {prd.get('status')}")
        source_type = prd.get("source_type")
        if source_type not in {"new", "legacy-brainstorm", "ad-hoc", "map-split", None}:
            errors.append(f"Invalid prd.source_type: {source_type}")
        validate_parent_map_pair(prd.get("parent_map"), prd.get("parent_initiative"), "prd", errors)
        if source_type == "map-split":
            if not prd.get("parent_map") or not prd.get("parent_initiative"):
                errors.append("prd.source_type map-split requires parent_map and parent_initiative")
            sizing = data.get("package_sizing") if isinstance(data.get("package_sizing"), dict) else {}
            if sizing.get("status") != "split_applied":
                errors.append("prd.source_type map-split requires package_sizing.status split_applied")
        if prd.get("status") == "ready-for-task":
            sizing = data.get("package_sizing") if isinstance(data.get("package_sizing"), dict) else {}
            if sizing.get("status") not in {"fits_package", "split_applied"}:
                errors.append("prd.status ready-for-task requires package_sizing.status fits_package or split_applied")

    tasks = data.get("tasks")
    if not isinstance(tasks, list):
        errors.append("tasks must be an array")
        tasks = []

    task_ids: set[str] = set()
    dependencies: dict[str, list[str]] = {}
    states_by_id: dict[str, str] = {}
    for task in tasks:
        if not isinstance(task, dict):
            errors.append("tasks[] entries must be objects")
            continue
        task_id = task.get("id")
        if not isinstance(task_id, str) or not TASK_ID_RE.match(task_id):
            errors.append(f"Invalid task id: {task_id}")
            continue
        if task_id in task_ids:
            errors.append(f"Duplicate task id: {task_id}")
        task_ids.add(task_id)
        for field in ["title", "milestone", "role", "state", "depends_on", "ready", "blockers", "attempts", "updated_at"]:
            if field not in task:
                errors.append(f"Missing field for {task_id}: {field}")
        if not isinstance(task.get("title"), str) or not task.get("title"):
            errors.append(f"title must be a non-empty string for {task_id}")
        if not isinstance(task.get("milestone"), str) or not task.get("milestone"):
            errors.append(f"milestone must be a non-empty string for {task_id}")
        if task.get("role") not in ROLES:
            errors.append(f"Invalid role for {task_id}: {task.get('role')}")
        state = task.get("state")
        if state not in TASK_STATES:
            errors.append(f"Invalid state for {task_id}: {state}")
        else:
            states_by_id[task_id] = state
        depends_on = task.get("depends_on", [])
        if not isinstance(depends_on, list) or not all(isinstance(dep, str) for dep in depends_on):
            errors.append(f"depends_on must be string array for {task_id}")
            depends_on = []
        if not isinstance(task.get("ready"), bool):
            errors.append(f"ready must be boolean for {task_id}")
        if not isinstance(task.get("blockers"), list) or not all(isinstance(item, str) for item in task.get("blockers", [])):
            errors.append(f"blockers must be string array for {task_id}")
        if not isinstance(task.get("attempts"), int) or task.get("attempts", 0) < 0:
            errors.append(f"attempts must be a non-negative integer for {task_id}")
        if task.get("ready") and task.get("blockers"):
            errors.append(f"Task {task_id} cannot be ready with blockers")
        if state == "ready" and not task.get("ready"):
            errors.append(f"Task {task_id} state is ready but ready=false")
        if task.get("ready") and state in {"needs_context", "blocked"}:
            errors.append(f"Task {task_id} ready=true conflicts with state {state}")
        source_amendment = task.get("source_amendment")
        if source_amendment is not None:
            if not isinstance(source_amendment, str) or not AMENDMENT_ID_RE.match(source_amendment):
                errors.append(f"source_amendment must be AMD-001 format for {task_id}")
            elif amendment_ids and source_amendment not in amendment_ids:
                errors.append(f"Task {task_id} references unknown source_amendment: {source_amendment}")
        corrects = task.get("corrects", [])
        if "corrects" in task:
            if not isinstance(corrects, list) or not all(isinstance(item, str) for item in corrects):
                errors.append(f"corrects must be string array for {task_id}")
                corrects = []
            elif task_id in corrects:
                errors.append(f"Task {task_id} cannot correct itself")
            for corrected in corrects:
                pending_amendment_task_refs.append((f"Task {task_id} corrects", task_id, corrected))
        dependencies[task_id] = depends_on

    if isinstance(prd, dict):
        for index, amendment in enumerate(prd.get("amendments", []) if isinstance(prd.get("amendments", []), list) else []):
            if not isinstance(amendment, dict):
                continue
            for affected in amendment.get("affects_tasks", []) if isinstance(amendment.get("affects_tasks", []), list) else []:
                if isinstance(affected, str) and TASK_ID_RE.match(affected) and affected not in task_ids:
                    errors.append(f"prd.amendments[{index}].affects_tasks references unknown task: {affected}")
    for label, task_id, referenced in pending_amendment_task_refs:
        if referenced not in task_ids:
            errors.append(f"{label} references unknown task: {referenced}")

    validate_package_sizing(data, errors)
    validate_execution(data, errors)

    if tasks:
        sizing = data.get("package_sizing") if isinstance(data.get("package_sizing"), dict) else {}
        if sizing.get("status") == "unchecked":
            errors.append("package_sizing.status is unchecked but task.json has tasks; brainstorm/map must resolve boundary sizing before T-xxx decomposition")
        if sizing.get("status") == "split_recommended":
            errors.append("package_sizing.status is split_recommended; route to map/package graph before adding package-local T-xxx")
        if sizing.get("status") not in {"fits_package", "split_applied"}:
            errors.append("task.json has tasks but package_sizing.status is not fits_package or split_applied")

    for task_id, deps in dependencies.items():
        for dep in deps:
            if dep not in task_ids:
                errors.append(f"Task {task_id} depends on unknown task {dep}")
            elif states_by_id.get(task_id) in {"in_progress", "done", "done_with_concerns", "approved", "approved_with_notes"} and states_by_id.get(dep) not in {"done", "done_with_concerns", "approved", "approved_with_notes", "skipped"}:
                errors.append(f"Task {task_id} is {states_by_id.get(task_id)} but dependency {dep} is {states_by_id.get(dep)}")

    errors.extend(find_cycles(dependencies))

    active_task = data.get("active_task")
    if active_task is not None:
        if active_task not in task_ids:
            errors.append(f"active_task points to unknown task: {active_task}")
        elif states_by_id.get(active_task) != "in_progress":
            errors.append(f"active_task {active_task} must have state in_progress, got {states_by_id.get(active_task)}")
    elif data.get("state") == "in_progress":
        errors.append("top-level state is in_progress but active_task is null")

    if isinstance(next_action, dict):
        next_task = next_action.get("task_id")
        if next_task is not None and next_task not in task_ids:
            errors.append(f"next_action.task_id points to unknown task: {next_task}")
        if next_action.get("skill") == "impl" and next_task and states_by_id.get(next_task) not in {"ready", "in_progress", "needs_rework"}:
            errors.append(f"next_action impl target {next_task} is not executable: {states_by_id.get(next_task)}")

    if data.get("state") == "reviewed" and active_task is not None:
        errors.append("top-level reviewed state cannot have active_task")
    if data.get("state") == "reviewed" and isinstance(next_action, dict) and next_action.get("skill") != "none":
        errors.append("top-level reviewed state should have next_action.skill=none")
    if data.get("state") == "reviewed":
        open_tasks = [task_id for task_id, task_state in states_by_id.items() if task_state not in REVIEW_PASS_STATES]
        if open_tasks:
            errors.append("top-level reviewed state requires all package-local tasks to be approved, approved_with_notes, or skipped: " + ", ".join(sorted(open_tasks)))
    if tasks and isinstance(prd, dict) and prd.get("status") == "draft" and any(states_by_id.get(task_id) in {"ready", "in_progress", "done", "done_with_concerns", "approved", "approved_with_notes"} for task_id in task_ids):
        errors.append("PRD is draft but task lifecycle has executable/completed tasks; run set-prd-status ready-for-task or revise PRD")
    if tasks and has_template_placeholders(pkg / "task.md"):
        errors.append("task.md still appears to contain template placeholders while task.json has tasks")
    if tasks:
        validate_task_markdown(pkg / "task.md", data, task_ids, errors)

    impl_entries = parse_jsonl(pkg / "context" / "impl.jsonl", errors, {"at", "actor", "task_id", "kind", "summary"})
    review_entries = parse_jsonl(pkg / "context" / "review.jsonl", errors, {"at", "actor", "task_id", "kind", "summary"})
    source_entries = parse_jsonl(pkg / "context" / "sources.jsonl", errors, {"id", "type", "location", "title", "why_it_matters"})

    for path_label, entries in [("impl", impl_entries), ("review", review_entries)]:
        for entry in entries:
            entry_task = entry.get("task_id")
            if entry_task is not None and entry_task not in task_ids:
                errors.append(f"context/{path_label}.jsonl references unknown task_id: {entry_task}")
            if entry.get("kind") not in CONTEXT_KINDS:
                errors.append(f"context/{path_label}.jsonl has invalid kind: {entry.get('kind')}")
    source_ids: set[str] = set()
    for entry in source_entries:
        source_id = entry.get("id")
        if source_id in source_ids:
            errors.append(f"Duplicate source id: {source_id}")
        if isinstance(source_id, str):
            source_ids.add(source_id)
        if entry.get("type") not in SOURCE_TYPES:
            errors.append(f"sources.jsonl has invalid type for {source_id}: {entry.get('type')}")

    history = data.get("phase_history", [])
    if not isinstance(history, list):
        errors.append("phase_history must be an array")
    else:
        for index, item in enumerate(history):
            if not isinstance(item, dict):
                errors.append(f"phase_history[{index}] must be an object")
                continue
            for field in ["at", "phase", "task_id", "from", "to", "actor", "note"]:
                if field not in item:
                    errors.append(f"phase_history[{index}] missing field: {field}")
            if item.get("phase") not in PHASES:
                errors.append(f"phase_history[{index}] has invalid phase: {item.get('phase')}")
            history_task = item.get("task_id")
            if history_task is not None and history_task not in task_ids:
                errors.append(f"phase_history[{index}] references unknown task_id: {history_task}")

    return errors


def find_cycles(graph: dict[str, list[str]]) -> list[str]:
    errors: list[str] = []
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str, path: list[str]) -> None:
        if node in visiting:
            cycle_start = path.index(node) if node in path else 0
            cycle = path[cycle_start:]
            errors.append("Dependency cycle: " + " -> ".join(cycle + [cycle[0]]))
            return
        if node in visited:
            return
        visiting.add(node)
        for dep in graph.get(node, []):
            if dep in graph:
                visit(dep, path + [dep])
        visiting.remove(node)
        visited.add(node)

    for node in graph:
        visit(node, [node])
    return errors
