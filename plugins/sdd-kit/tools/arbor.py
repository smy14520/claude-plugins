#!/usr/bin/env python3
"""Deterministic filesystem/state helper for sdd-kit task packages.

This script intentionally avoids semantic decisions. It creates and validates
package structure, appends JSONL context, and updates task lifecycle metadata.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "arbor-task-v1"
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
TASK_ID_RE = re.compile(r"^T-\d{3}$")

MODES = {"strict-atomic", "lean"}
TOP_LEVEL_STATES = {
    "planned",
    "ready",
    "in_progress",
    "needs_context",
    "blocked",
    "impl_done",
    "reviewed",
    "needs_rework",
    "brainstorm_drift",
    "completed",
    "superseded",
}
TASK_STATES = {
    "planned",
    "ready",
    "in_progress",
    "done",
    "done_with_concerns",
    "needs_context",
    "blocked",
    "approved",
    "approved_with_notes",
    "needs_rework",
    "brainstorm_drift",
    "skipped",
}
PHASES = {"brainstorm", "task", "impl", "self_check", "review", "complete"}
NEXT_ACTION_SKILLS = {"brainstorm", "task", "impl", "review", "user", "none"}
CONTEXT_TYPES = {"impl", "review", "sources"}
CONTEXT_KINDS = {"constraint", "source", "note", "acceptance", "risk", "decision", "file", "command"}
SOURCE_TYPES = {"local-file", "research-note", "external-url", "wiki", "task", "other"}
ROLES = {"backend", "frontend", "data", "devops", "shared", "test", "docs", "fullstack"}


class ArborError(Exception):
    """User-facing CLI error."""


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


def base_task_json(name: str, mode: str, title: str, timestamp: str, source_type: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "name": name,
        "title": title,
        "package_path": f".arbor/tasks/{name}",
        "created_at": timestamp,
        "updated_at": timestamp,
        "completed_at": None,
        "prd": {
            "file": "prd.md",
            "status": "draft",
            "source_type": source_type,
            "legacy_source": f".arbor/brainstorms/{name}.md" if source_type == "legacy-brainstorm" else None,
            "ready_for_task_at": None,
        },
        "definition": {
            "task_md": "task.md",
            "frozen": False,
            "version": 0,
            "updated_at": None,
        },
        "mode": mode,
        "state": "planned",
        "current_phase": "brainstorm",
        "active_task": None,
        "next_action": {
            "skill": "brainstorm",
            "task_id": None,
            "reason": "prd draft created",
        },
        "tasks": [],
        "phase_history": [
            {
                "at": timestamp,
                "phase": "brainstorm",
                "task_id": None,
                "from": None,
                "to": "planned",
                "actor": "arbor",
                "note": "task package created",
            }
        ],
    }


def prd_template(name: str, title: str, timestamp: str) -> str:
    date = timestamp[:10]
    return f"""---
name: {name}
status: draft
date: {date}
package: .arbor/tasks/{name}/
tags: []
supersedes:
---

# {title}

<!-- 输出语言: 中文 -->
<!-- Package-local PRD/context artifact. Brainstorm skill owns this file. -->

## 背景与问题

<为什么现在要做这件事？当前痛点 / 触发条件 / 业务上下文是什么？>

## 目标 / Desired outcomes

- <本次 change 交付的结果 1>
- <结果 2>

## 本次范围

### In scope

- <本次明确要做的内容 1>

### Out of scope

- <看起来相近，但本次明确不做的内容 1>

## 关键场景 / 用户流 / 系统流

### 场景 1 — <名称>

- 触发:
- 预期行为:
- 成功判定:
- 备注 / 来源: [SRC-...]

### 边界 / 异常场景

- <边界场景 1>

## 交付物清单

- <接口 / 页面 / 模块 / 脚本 / 配置 / 数据变更>

## 方案草图 / Proposed approach

<高层方案。强调如何满足场景与交付物，不写实现步骤流水账。>

## 拆解线索 / 实现切片建议

- Slice A:
- Slice B:
- 依赖顺序 / 并行性提示:

## 关键约束（仅保留承重约束）

- <真正会影响 task 拆解或实现边界的约束>

## 验证重点

- <必须验证的行为 1>

## 风险 / 开放问题 / 假设

### Open questions

- <会影响 task 拆解的未决项>

### Assumptions

- <当前暂时成立的前提>

### Risks

- <继续推进时必须显式暴露的风险>

## Sources

| ID | Type | Location | Title | Why it matters |
|----|------|----------|-------|----------------|
| SRC-LOCAL-001 | local-file | `src/...:12-48` | <title> | <why> |

<!--
═══ 自检清单 (Finalize 前逐项确认, 确认后删除本块) ═══
- [ ] 背景说明了“为什么现在做”
- [ ] In scope / Out of scope 足够明确
- [ ] 至少写出 2 个关键场景（如适用）
- [ ] 交付物清单可被 task 直接拿来拆
- [ ] 拆解线索给出了切片或顺序提示
- [ ] Open questions / Assumptions / Risks 已分开
- [ ] Sources 能覆盖关键判断，不只是装饰附录
- [ ] 若进入 task，不会因缺少关键信息而立刻卡住
════════════════════════════════════════════════════ -->
"""


def task_template(name: str, mode: str, timestamp: str) -> str:
    date = timestamp[:10]
    return f"""---
package: {name}
source: prd.md
source_type: package-prd
mode: {mode}
date: {date}
---

# 任务: {name}

<!-- 输出语言: 中文 -->
<!--
  任务定义约定（强制执行）：
  - 禁止 wikilinks。本文件应自包含。
  - 禁止高层决策。每个任务仅包含可执行操作。
  - ID 只允许追加，不得重新编号。
  - 每条验收条件必须是可执行命令或二元谓词。
  - 每个任务必须有 task-local context、sources 和 ready-check。
  - impl 不得修改本文件；执行状态只写入 task.json。
  - review 不得修改本文件；审计记录追加到 review.md，latest review state 写入 task.json。
-->

## 概览

- 来源: `prd.md`
- 模式: {mode}
- 总任务数: <N>
- milestone 数: <N>
- 总预估工时: <hours>
- 关键路径: <T-xxx → T-yyy → T-zzz = Nh>

## Milestones

### M-01 — <里程碑名称>

- 目标:
- 包含任务: [T-001]
- 完成判定:

## 依赖关系图

```text
M-01
  T-001 (shared)
```

## 任务列表

- id: T-001
  milestone: M-01
  role: shared
  title: "ADD <deliverable>"
  deliverable: "<path or behavior>"
  depends-on: []
  context: |
    <task-local context; do not require impl to reread full PRD>
  sources:
    - SRC-LOCAL-001
  ready-check: |
    - ready: true
    - blockers: []
  acceptance: |
    - <binary predicate or command>
  estimate: 2h
  notes: ""
"""


def review_template(name: str, timestamp: str) -> str:
    date = timestamp[:10]
    return f"""---
task: {name}
updated: {date}
---

# Review log: {name}

Append-only semantic audit entries. Current lifecycle state lives in `task.json`.
"""


def create_package(root: Path, name: str, mode: str, title: str | None, source_type: str, timestamp: str) -> dict[str, Any]:
    validate_name(name)
    if mode not in MODES:
        raise ArborError(f"Invalid mode '{mode}'. Expected one of: {', '.join(sorted(MODES))}.")
    if source_type not in {"new", "legacy-brainstorm", "ad-hoc"}:
        raise ArborError("Invalid source type. Expected new, legacy-brainstorm, or ad-hoc.")

    title = title or name
    pkg = package_dir(root, name)
    context_dir = pkg / "context"
    context_dir.mkdir(parents=True, exist_ok=True)

    created_files: list[str] = []
    for rel, content in [
        ("prd.md", prd_template(name, title, timestamp)),
        ("task.md", task_template(name, mode, timestamp)),
        ("review.md", review_template(name, timestamp)),
        ("context/impl.jsonl", ""),
        ("context/review.jsonl", ""),
        ("context/sources.jsonl", ""),
    ]:
        if write_if_missing(pkg / rel, content):
            created_files.append(rel)

    task_path = task_json_path(pkg)
    if task_path.exists():
        data = read_json(task_path)
    else:
        data = base_task_json(name, mode, title, timestamp, source_type)
        write_json(task_path, data)
        created_files.append("task.json")

    return {"package": str(pkg), "created": created_files, "already_exists": not bool(created_files)}


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
    return "<" in text and ">" in text


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

    prd = data.get("prd")
    if not isinstance(prd, dict):
        errors.append("prd must be an object")
    else:
        if prd.get("file") != "prd.md":
            errors.append("prd.file must be prd.md")
        if prd.get("status") not in {"draft", "ready-for-task", "revising", "superseded"}:
            errors.append(f"Invalid prd.status: {prd.get('status')}")

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
        dependencies[task_id] = depends_on

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
    if tasks and isinstance(prd, dict) and prd.get("status") == "draft" and any(states_by_id.get(task_id) in {"ready", "in_progress", "done", "done_with_concerns", "approved", "approved_with_notes"} for task_id in task_ids):
        errors.append("PRD is draft but task lifecycle has executable/completed tasks; run set-prd-status ready-for-task or revise PRD")
    if tasks and has_template_placeholders(pkg / "task.md"):
        errors.append("task.md still appears to contain template placeholders while task.json has tasks")

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


def add_phase_history(data: dict[str, Any], timestamp: str, phase: str, task_id: str | None, from_state: str | None, to_state: str, actor: str, note: str) -> None:
    data.setdefault("phase_history", []).append(
        {
            "at": timestamp,
            "phase": phase,
            "task_id": task_id,
            "from": from_state,
            "to": to_state,
            "actor": actor,
            "note": note,
        }
    )


def update_task_status(root: Path, name: str, task_id: str | None, state: str, actor: str, note: str, timestamp: str) -> dict[str, Any]:
    pkg, data = load_package(root, name)
    if task_id:
        if state not in TASK_STATES:
            raise ArborError(f"Invalid task state '{state}'.")
        task = find_task(data, task_id)
        old = task.get("state")
        task["state"] = state
        task["updated_at"] = timestamp
        if state == "in_progress":
            task["attempts"] = int(task.get("attempts") or 0) + 1
            data["state"] = "in_progress"
            data["current_phase"] = "impl"
            data["active_task"] = task_id
            data["next_action"] = {"skill": "impl", "task_id": task_id, "reason": "implementation in progress"}
        elif state in {"done", "done_with_concerns"}:
            task["last_impl_result"] = {
                "state": "DONE" if state == "done" else "DONE_WITH_CONCERNS",
                "at": timestamp,
                "summary": note,
                "acceptance": [],
                "concerns": [],
            }
            data["state"] = "impl_done"
            data["current_phase"] = "impl"
            if data.get("active_task") == task_id:
                data["active_task"] = None
            data["next_action"] = {
                "skill": "review",
                "task_id": task_id,
                "reason": "implementation reported done; semantic audit pending",
            }
        elif state == "needs_context":
            task["last_impl_result"] = {
                "state": "NEEDS_CONTEXT",
                "at": timestamp,
                "summary": note,
                "acceptance": [],
                "concerns": [],
            }
            data["state"] = "needs_context"
            data["current_phase"] = "task"
            if data.get("active_task") == task_id:
                data["active_task"] = None
            data["next_action"] = {"skill": "task", "task_id": task_id, "reason": "task-local context is missing or conflicting"}
        elif state == "blocked":
            task["last_impl_result"] = {
                "state": "BLOCKED",
                "at": timestamp,
                "summary": note,
                "acceptance": [],
                "concerns": [],
            }
            data["state"] = "blocked"
            if data.get("active_task") == task_id:
                data["active_task"] = None
            data["next_action"] = {"skill": "user", "task_id": task_id, "reason": "external blocker requires user action"}
        elif state in {"approved", "approved_with_notes"}:
            task["last_review_result"] = {
                "state": "APPROVED" if state == "approved" else "APPROVED_WITH_NOTES",
                "at": timestamp,
                "summary": note,
                "evidence": [],
                "notes": [],
            }
            data["state"] = "reviewed"
            data["current_phase"] = "review"
            if data.get("active_task") == task_id:
                data["active_task"] = None
            data["next_action"] = {"skill": "none", "task_id": None, "reason": "semantic audit passed for this task"}
        elif state == "needs_rework":
            task["last_review_result"] = {
                "state": "NEEDS_REWORK",
                "at": timestamp,
                "summary": note,
                "evidence": [],
                "notes": [],
            }
            data["state"] = "needs_rework"
            data["current_phase"] = "review"
            data["next_action"] = {"skill": "impl", "task_id": task_id, "reason": "review found rework required"}
        elif state == "brainstorm_drift":
            task["last_review_result"] = {
                "state": "BRAINSTORM_DRIFT",
                "at": timestamp,
                "summary": note,
                "evidence": [],
                "notes": [],
            }
            data["state"] = "brainstorm_drift"
            data["current_phase"] = "review"
            data["next_action"] = {"skill": "brainstorm", "task_id": task_id, "reason": "package PRD is stale or incorrect"}
        elif state == "skipped":
            if data.get("active_task") == task_id:
                data["active_task"] = None
        add_phase_history(data, timestamp, data.get("current_phase", "task"), task_id, old, state, actor, note)
    else:
        if state not in TOP_LEVEL_STATES:
            raise ArborError(f"Invalid top-level state '{state}'.")
        old = data.get("state")
        data["state"] = state
        add_phase_history(data, timestamp, data.get("current_phase", "task"), None, old, state, actor, note)
    data["updated_at"] = timestamp
    save_package(pkg, data)
    return data


def update_phase(root: Path, name: str, phase: str, actor: str, note: str, task_id: str | None, timestamp: str) -> dict[str, Any]:
    if phase not in PHASES:
        raise ArborError(f"Invalid phase '{phase}'.")
    pkg, data = load_package(root, name)
    if task_id:
        find_task(data, task_id)
    old = data.get("current_phase")
    data["current_phase"] = phase
    data["updated_at"] = timestamp
    add_phase_history(data, timestamp, phase, task_id, old, phase, actor, note)
    save_package(pkg, data)
    return data


def update_prd_status(root: Path, name: str, status: str, actor: str, note: str, timestamp: str) -> dict[str, Any]:
    if status not in {"draft", "ready-for-task", "revising", "superseded"}:
        raise ArborError(f"Invalid PRD status '{status}'.")
    pkg, data = load_package(root, name)
    prd = data.setdefault("prd", {})
    old = prd.get("status")
    prd["status"] = status
    if status == "ready-for-task":
        prd["ready_for_task_at"] = timestamp
        data["state"] = "ready"
        data["current_phase"] = "task"
        data["next_action"] = {"skill": "task", "task_id": None, "reason": "prd ready for task decomposition"}
    elif status in {"draft", "revising"}:
        data["current_phase"] = "brainstorm"
        data["next_action"] = {"skill": "brainstorm", "task_id": None, "reason": "prd is not ready for task decomposition"}
    elif status == "superseded":
        data["state"] = "superseded"
        data["next_action"] = {"skill": "user", "task_id": None, "reason": "prd was superseded"}
    data["updated_at"] = timestamp
    add_phase_history(data, timestamp, data.get("current_phase", "brainstorm"), None, old, status, actor, note)
    save_package(pkg, data)
    return data


def freeze_definition(root: Path, name: str, actor: str, note: str, timestamp: str) -> dict[str, Any]:
    pkg, data = load_package(root, name)
    definition = data.setdefault("definition", {})
    old = "frozen" if definition.get("frozen") else "draft"
    definition["task_md"] = definition.get("task_md") or "task.md"
    definition["frozen"] = True
    definition["version"] = int(definition.get("version") or 0) + 1
    definition["updated_at"] = timestamp
    data["state"] = "ready"
    data["current_phase"] = "task"
    ready_tasks = [task for task in data.get("tasks", []) if task.get("state") == "ready"]
    if ready_tasks:
        first = sorted(ready_tasks, key=lambda task: task.get("id", ""))[0]
        data["next_action"] = {"skill": "impl", "task_id": first.get("id"), "reason": "task definition frozen; first ready task"}
    else:
        data["next_action"] = {"skill": "user", "task_id": None, "reason": "task definition frozen but no ready tasks"}
    data["updated_at"] = timestamp
    add_phase_history(data, timestamp, "task", None, old, "frozen", actor, note)
    save_package(pkg, data)
    return data


def find_task(data: dict[str, Any], task_id: str) -> dict[str, Any]:
    for task in data.get("tasks", []):
        if task.get("id") == task_id:
            return task
    raise ArborError(f"Unknown task id: {task_id}")


def add_child(root: Path, name: str, task_id: str, title: str, milestone: str, role: str, depends_on: list[str], ready: bool, blockers: list[str], timestamp: str) -> dict[str, Any]:
    if not TASK_ID_RE.match(task_id):
        raise ArborError(f"Invalid task id '{task_id}'. Use T-001 format.")
    if role not in ROLES:
        raise ArborError(f"Invalid role '{role}'.")
    pkg, data = load_package(root, name)
    tasks = data.setdefault("tasks", [])
    existing_ids = {task.get("id") for task in tasks}
    if task_id in existing_ids:
        raise ArborError(f"Task already exists: {task_id}")
    for dep in depends_on:
        if dep and dep not in existing_ids:
            raise ArborError(f"Dependency does not exist: {dep}")
    state = "ready" if ready and not blockers else "needs_context"
    task = {
        "id": task_id,
        "title": title,
        "milestone": milestone,
        "role": role,
        "state": state,
        "depends_on": [dep for dep in depends_on if dep],
        "ready": ready and not blockers,
        "blockers": blockers,
        "attempts": 0,
        "last_impl_result": None,
        "last_review_result": None,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    tasks.append(task)
    data["updated_at"] = timestamp
    if data.get("next_action", {}).get("skill") in {"brainstorm", "task"} and task["ready"]:
        data["next_action"] = {"skill": "impl", "task_id": task_id, "reason": "first ready task"}
    add_phase_history(data, timestamp, data.get("current_phase", "task"), task_id, None, state, "task", "child task added")
    save_package(pkg, data)
    return data


def add_context(root: Path, name: str, context_type: str, task_id: str | None, kind: str | None, summary: str | None, source: str | None, actor: str, timestamp: str, source_id: str | None, source_type: str | None, location: str | None, title: str | None, why: str | None) -> dict[str, Any]:
    if context_type not in CONTEXT_TYPES:
        raise ArborError(f"Invalid context type '{context_type}'.")
    pkg, data = load_package(root, name)
    if task_id:
        find_task(data, task_id)
    path = pkg / "context" / f"{context_type}.jsonl"
    if context_type == "sources":
        if not all([source_id, source_type, location, title, why]):
            raise ArborError("sources context requires --source-id, --source-type, --location, --title, and --why.")
        if source_type not in SOURCE_TYPES:
            raise ArborError(f"Invalid source type '{source_type}'.")
        entry = {
            "id": source_id,
            "type": source_type,
            "location": location,
            "title": title,
            "why_it_matters": why,
        }
    else:
        if not summary:
            raise ArborError("impl/review context requires --summary.")
        if kind and kind not in CONTEXT_KINDS:
            raise ArborError(f"Invalid context kind '{kind}'.")
        entry = {
            "at": timestamp,
            "actor": actor,
            "task_id": task_id,
            "kind": kind or "note",
            "source": source,
            "summary": summary,
        }
    append_jsonl(path, entry)
    data["updated_at"] = timestamp
    save_package(pkg, data)
    return entry


def list_packages(root: Path) -> list[dict[str, Any]]:
    root_dir = tasks_root(root)
    if not root_dir.exists():
        return []
    result: list[dict[str, Any]] = []
    for pkg in sorted(path for path in root_dir.iterdir() if path.is_dir()):
        task_path = pkg / "task.json"
        if not task_path.exists():
            continue
        try:
            data = read_json(task_path)
        except ArborError:
            continue
        tasks = data.get("tasks", []) if isinstance(data.get("tasks"), list) else []
        result.append(
            {
                "name": pkg.name,
                "state": data.get("state"),
                "current_phase": data.get("current_phase"),
                "active_task": data.get("active_task"),
                "next_action": data.get("next_action"),
                "task_count": len(tasks),
                "ready_count": sum(1 for task in tasks if task.get("state") == "ready"),
                "blocked_count": sum(1 for task in tasks if task.get("state") in {"blocked", "needs_context"}),
            }
        )
    return result


def show_package(root: Path, name: str) -> dict[str, Any]:
    pkg, data = load_package(root, name)
    errors = validate_package(root, name)
    tasks = data.get("tasks", []) if isinstance(data.get("tasks"), list) else []
    return {
        "name": name,
        "package": str(pkg),
        "state": data.get("state"),
        "current_phase": data.get("current_phase"),
        "active_task": data.get("active_task"),
        "next_action": data.get("next_action"),
        "prd": data.get("prd"),
        "tasks": tasks,
        "validation": {"ok": not errors, "errors": errors},
    }


def print_human_list(items: list[dict[str, Any]]) -> None:
    if not items:
        print("No task packages found.")
        return
    for item in items:
        next_action = item.get("next_action") or {}
        print(
            f"{item['name']}\tstate={item.get('state')}\tphase={item.get('current_phase')}\t"
            f"active={item.get('active_task')}\tnext={next_action.get('skill')}:{next_action.get('task_id')}\t"
            f"tasks={item.get('task_count')} ready={item.get('ready_count')} blocked={item.get('blocked_count')}"
        )


def print_human_show(data: dict[str, Any]) -> None:
    print(f"Package: {data['name']}")
    print(f"Path: {data['package']}")
    print(f"State: {data.get('state')}")
    print(f"Phase: {data.get('current_phase')}")
    print(f"Active task: {data.get('active_task')}")
    print(f"Next action: {data.get('next_action')}")
    print(f"PRD: {data.get('prd')}")
    print(f"Validation: {'ok' if data['validation']['ok'] else 'failed'}")
    for error in data["validation"]["errors"]:
        print(f"  - {error}")
    if data.get("tasks"):
        print("Tasks:")
        for task in data["tasks"]:
            print(f"  - {task.get('id')} {task.get('state')} {task.get('title')}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage sdd-kit Arbor task packages.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Project root containing .arbor/.")
    parser.add_argument("--now", help="Override timestamp for deterministic tests.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output for list/show/create.")
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create", help="Create a task package.")
    create.add_argument("name")
    create.add_argument("--mode", choices=sorted(MODES), default="strict-atomic")
    create.add_argument("--title")
    create.add_argument("--source-type", choices=["new", "legacy-brainstorm", "ad-hoc"], default="new")
    create.add_argument("--json", dest="json_output", action="store_true", help="Emit JSON output.")

    validate = sub.add_parser("validate", help="Validate one or all task packages.")
    target = validate.add_mutually_exclusive_group(required=True)
    target.add_argument("name", nargs="?")
    target.add_argument("--all", action="store_true")

    set_status = sub.add_parser("set-status", help="Update package or task state.")
    set_status.add_argument("name")
    set_status.add_argument("--task")
    set_status.add_argument("--state", required=True)
    set_status.add_argument("--actor", required=True)
    set_status.add_argument("--note", default="")

    set_phase = sub.add_parser("set-phase", help="Update current phase.")
    set_phase.add_argument("name")
    set_phase.add_argument("--phase", required=True)
    set_phase.add_argument("--task")
    set_phase.add_argument("--actor", required=True)
    set_phase.add_argument("--note", default="")

    set_prd = sub.add_parser("set-prd-status", help="Update PRD readiness status.")
    set_prd.add_argument("name")
    set_prd.add_argument("--status", required=True, choices=["draft", "ready-for-task", "revising", "superseded"])
    set_prd.add_argument("--actor", required=True)
    set_prd.add_argument("--note", default="")

    freeze = sub.add_parser("freeze-definition", help="Mark task.md as frozen and ready for implementation.")
    freeze.add_argument("name")
    freeze.add_argument("--actor", required=True)
    freeze.add_argument("--note", default="")

    add_child_parser = sub.add_parser("add-child", help="Add a task lifecycle record.")
    add_child_parser.add_argument("name")
    add_child_parser.add_argument("--id", required=True)
    add_child_parser.add_argument("--title", required=True)
    add_child_parser.add_argument("--milestone", required=True)
    add_child_parser.add_argument("--role", required=True, choices=sorted(ROLES))
    add_child_parser.add_argument("--depends-on", default="")
    add_child_parser.add_argument("--ready", choices=["true", "false"], default="true")
    add_child_parser.add_argument("--blocker", action="append", default=[])

    add_ctx = sub.add_parser("add-context", help="Append context JSONL.")
    add_ctx.add_argument("name")
    add_ctx.add_argument("--type", required=True, choices=sorted(CONTEXT_TYPES))
    add_ctx.add_argument("--task")
    add_ctx.add_argument("--kind", choices=sorted(CONTEXT_KINDS))
    add_ctx.add_argument("--source")
    add_ctx.add_argument("--summary")
    add_ctx.add_argument("--actor", default="task")
    add_ctx.add_argument("--source-id")
    add_ctx.add_argument("--source-type", choices=sorted(SOURCE_TYPES))
    add_ctx.add_argument("--location")
    add_ctx.add_argument("--title")
    add_ctx.add_argument("--why")

    list_parser = sub.add_parser("list", help="List task packages.")
    list_parser.add_argument("--json", dest="json_output", action="store_true", help="Emit JSON output.")

    show = sub.add_parser("show", help="Show one task package.")
    show.add_argument("name")
    show.add_argument("--json", dest="json_output", action="store_true", help="Emit JSON output.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = args.root.resolve()
    timestamp = now_iso(args.now)
    json_output = getattr(args, "json_output", False) or args.json
    try:
        if args.command == "create":
            result = create_package(root, args.name, args.mode, args.title, args.source_type, timestamp)
            if json_output:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(f"Package: {result['package']}")
                if result["created"]:
                    print("Created: " + ", ".join(result["created"]))
                else:
                    print("Package already existed; no files overwritten.")
            return 0

        if args.command == "validate":
            targets = [item["name"] for item in list_packages(root)] if args.all else [args.name]
            all_errors: dict[str, list[str]] = {}
            for name in targets:
                errors = validate_package(root, name)
                if errors:
                    all_errors[name] = errors
            if json_output:
                print(json.dumps({"ok": not all_errors, "errors": all_errors}, ensure_ascii=False, indent=2))
            elif all_errors:
                for name, errors in all_errors.items():
                    print(f"{name}: failed")
                    for error in errors:
                        print(f"  - {error}")
            else:
                print("ok")
            return 1 if all_errors else 0

        if args.command == "set-status":
            update_task_status(root, args.name, args.task, args.state, args.actor, args.note, timestamp)
            print("ok")
            return 0

        if args.command == "set-phase":
            update_phase(root, args.name, args.phase, args.actor, args.note, args.task, timestamp)
            print("ok")
            return 0

        if args.command == "set-prd-status":
            update_prd_status(root, args.name, args.status, args.actor, args.note, timestamp)
            print("ok")
            return 0

        if args.command == "freeze-definition":
            freeze_definition(root, args.name, args.actor, args.note, timestamp)
            print("ok")
            return 0

        if args.command == "add-child":
            deps = [item.strip() for item in args.depends_on.split(",") if item.strip()]
            ready = args.ready == "true"
            add_child(root, args.name, args.id, args.title, args.milestone, args.role, deps, ready, args.blocker, timestamp)
            print("ok")
            return 0

        if args.command == "add-context":
            add_context(
                root,
                args.name,
                args.type,
                args.task,
                args.kind,
                args.summary,
                args.source,
                args.actor,
                timestamp,
                args.source_id,
                args.source_type,
                args.location,
                args.title,
                args.why,
            )
            print("ok")
            return 0

        if args.command == "list":
            items = list_packages(root)
            if json_output:
                print(json.dumps(items, ensure_ascii=False, indent=2))
            else:
                print_human_list(items)
            return 0

        if args.command == "show":
            result = show_package(root, args.name)
            if json_output:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print_human_show(result)
            return 0

        parser.error(f"Unhandled command {args.command}")
        return 2
    except ArborError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
