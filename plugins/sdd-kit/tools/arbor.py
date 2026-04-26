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
MAP_SCHEMA_VERSION = "arbor-map-v1"
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
PHASES = {"brainstorm", "map", "task", "impl", "self_check", "review", "complete"}
NEXT_ACTION_SKILLS = {"brainstorm", "map", "task", "impl", "review", "user", "none"}
CONTEXT_TYPES = {"impl", "review", "sources"}
CONTEXT_KINDS = {"constraint", "source", "note", "acceptance", "risk", "decision", "file", "command"}
SOURCE_TYPES = {"local-file", "research-note", "external-url", "wiki", "task", "other"}
ROLES = {"backend", "frontend", "data", "devops", "shared", "test", "docs", "fullstack"}
EXECUTION_STATUSES = {"unclaimed", "claimed", "released", "worktree_ready", "in_progress", "impl_done", "reviewed", "pr_open", "merged", "abandoned"}
PR_STATES = {"none", "draft", "open", "merged", "closed", "not_applicable"}
AGENT_RECORD_ROLES = {"impl", "review", "test", "validation"}
AGENT_RECORD_STATUSES = {"planned", "running", "passed", "failed", "blocked"}
PACKAGE_SIZING_STATUSES = {"unchecked", "fits_package", "split_recommended", "split_applied"}
CHILD_TASK_EXECUTION_FIELDS = {"branch", "worktree", "pr", "execution"}
DEPENDENCY_COMPLETE_STATES = {"done", "done_with_concerns", "approved", "approved_with_notes", "skipped"}
REVIEW_PASS_STATES = {"approved", "approved_with_notes", "skipped"}


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


def maps_root(root: Path) -> Path:
    return arbor_root(root) / "maps"


def map_dir(root: Path, initiative: str) -> Path:
    validate_name(initiative)
    return maps_root(root) / initiative


def map_path(root: Path, initiative: str) -> Path:
    return map_dir(root, initiative) / "map.md"


def map_json_path(root: Path, initiative: str) -> Path:
    return map_dir(root, initiative) / "map.json"


def map_context_dir(root: Path, initiative: str) -> Path:
    return map_dir(root, initiative) / "context"


def legacy_map_path(root: Path, initiative: str) -> Path:
    validate_name(initiative)
    return maps_root(root) / f"{initiative}.md"


def parent_map_ref(initiative: str) -> str:
    validate_name(initiative)
    return f".arbor/maps/{initiative}/map.md"


def legacy_parent_map_ref(initiative: str) -> str:
    validate_name(initiative)
    return f".arbor/maps/{initiative}.md"


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


def default_execution(name: str) -> dict[str, Any]:
    return {
        "boundary": "package",
        "unit_path": f".arbor/tasks/{name}",
        "child_task_scope": "control_acceptance_review",
        "status": "unclaimed",
        "owner": None,
        "claimed_at": None,
        "released_at": None,
        "branch": {
            "base": None,
            "name": None,
            "upstream": None,
        },
        "worktree": {
            "path": None,
            "created_by": None,
        },
        "session": None,
        "pr": {
            "url": None,
            "number": None,
            "state": "none",
        },
        "agents": [],
        "updated_at": None,
        "updated_by": None,
        "note": None,
    }


def ensure_execution(data: dict[str, Any]) -> dict[str, Any]:
    name = data.get("name")
    if not isinstance(name, str):
        name = ""
    execution = data.get("execution")
    if not isinstance(execution, dict):
        execution = default_execution(name)
        data["execution"] = execution
        return execution

    defaults = default_execution(name)
    for key, value in defaults.items():
        if key not in execution:
            execution[key] = value
    for key in ["branch", "worktree", "pr"]:
        if not isinstance(execution.get(key), dict):
            execution[key] = defaults[key]
        else:
            for child_key, child_value in defaults[key].items():
                execution[key].setdefault(child_key, child_value)
    if not isinstance(execution.get("agents"), list):
        execution["agents"] = []
    return execution


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
        "package_sizing": {
            "status": "unchecked",
            "decision": None,
            "signals": [],
            "recommended_packages": [],
            "decided_at": None,
            "decided_by": None,
            "note": None,
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
        "execution": default_execution(name),
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
<!-- Executable package PRD/context artifact. Brainstorm skill owns this file after boundary routing. -->

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

## Boundary sizing decision

- Boundary status: <fits_package | split_applied>
- Parent map / initiative: <.arbor/maps/<initiative>/map.md | none>
- Why this is one executable package: <为什么当前范围可以用一个 branch/worktree/PR review 和回滚>
- Expected branch/worktree/PR: one
- Rejected split candidates: <哪些 slice 被考虑过但不需要独立 package；原因是什么>
- T-xxx 语义: package-local control / acceptance / review 单元，不默认创建独立 branch/worktree/PR
- 多 agent 使用: <是否允许多个 agent 在同一 package boundary 内协作；如需要跨 package 并行，交给 map 管理>

## 拆解线索 / 实现切片建议

- Slice A:
- Slice B:
- 依赖顺序 / 并行性提示:
- 注意: 这些 slice 后续会变成 package-local T-xxx；不是独立 PR 单元

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
- [ ] Boundary sizing decision 已明确为 fits_package 或 split_applied
- [ ] Package 可作为一个 branch/worktree/PR 执行边界；若不能，未 finalize 本文件，已路由到 `.arbor/maps/<initiative>/map.md`
- [ ] 拆解线索给出了切片或顺序提示，且 slice 只是 package-local T-xxx 候选
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
  - ID 只允许追加，不得重新编号；T-xxx 只在本 package 内唯一。
  - Package 是 branch/worktree/PR 执行边界；T-xxx 是 package-local control / acceptance / review 单元。
  - 不要为每个 T-xxx 默认创建独立 branch/worktree/PR；如需独立 PR，应拆成新的 package。
  - 每条验收条件必须是可执行命令或二元谓词。
  - 每个任务必须有 task-local context、sources 和 ready-check。
  - impl 不得修改本文件；执行状态只写入 task.json。
  - review 不得修改本文件；审计记录追加到 review.md，latest review state 写入 task.json。
-->

## 概览

- 来源: `prd.md`
- 模式: {mode}
- Package execution boundary: `.arbor/tasks/{name}/`（一个 package 默认对应一个 branch/worktree/PR）
- T-xxx scope: package-local control / acceptance / review，不是默认 PR 单元
- Boundary sizing decision from brainstorm/map: <fits_package | split_applied> — <为什么当前 package 边界成立；若拆过，列出来源/去向 package>
- Parent map / initiative: <.arbor/maps/<initiative>/map.md | none>
- Package PR readiness: 所有 required T-xxx 通过 review，且无 package-level blocker
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

Append-only semantic audit entries for package-local T-xxx control units.
Current lifecycle state lives in `task.json`.
A single T-xxx approval does not mean the package branch/worktree/PR is ready; package readiness is aggregated from all required child tasks.
"""


def map_template(initiative: str, title: str, timestamp: str) -> str:
    date = timestamp[:10]
    return f"""---
initiative: {initiative}
status: draft
date: {date}
map_json: map.json
---

# {title}

<!-- 输出语言: 中文 -->
<!-- Large initiative package graph. Map skill owns this file; map.json is the machine-readable coordination source. -->

## 当前 framing

<这个 initiative 为什么需要多个 executable packages？>

## Package graph

| Package | Materialized | Depends on | Wave | Boundary reason | PRD status | Execution status | Notes |
|---|---|---|---|---|---|---|---|
| `.arbor/tasks/<package>/` | no | [] | W1 | <why this is one executable package> | draft | unclaimed | <notes> |

## Cross-package contracts

- <package-a> → <package-b>: <contract / dependency>

## Execution waves

- W1: <packages with no package dependency blockers>
- W2: <packages unlocked after W1 package review/completion>

## Current blockers

- <blocker>

## Next orchestration check

Run:

```text
python3 plugins/sdd-kit/tools/arbor.py map-check {initiative}
python3 plugins/sdd-kit/tools/arbor.py map-plan-agents {initiative} --max-parallel 2
```
"""


def base_map_json(initiative: str, title: str, timestamp: str) -> dict[str, Any]:
    return {
        "schema_version": MAP_SCHEMA_VERSION,
        "initiative": initiative,
        "title": title,
        "map_path": parent_map_ref(initiative),
        "status": "draft",
        "created_at": timestamp,
        "updated_at": timestamp,
        "packages": [],
        "orchestration": {
            "default_max_parallel": 2,
            "strategy": "autonomous-package-pipeline",
            "dependency_gate": "dependencies must be reviewed/completed before downstream package assignment",
            "context_injection": "map.md + map.json + package task.json/prd/task/context + dependency summaries",
            "manual_review_mode": "use explicit brainstorm/task/impl/review skills instead of parallel",
        },
        "history": [
            {
                "at": timestamp,
                "actor": "arbor",
                "event": "map_created",
                "note": "initiative map workspace created",
            }
        ],
    }


def create_map(root: Path, initiative: str, title: str | None, timestamp: str, status: str | None = "draft") -> dict[str, Any]:
    validate_name(initiative)
    if status is not None and status not in {"draft", "active", "ready", "closed", "superseded"}:
        raise ArborError(f"Invalid map status '{status}'.")
    title = title or initiative
    directory = map_dir(root, initiative)
    context_dir = map_context_dir(root, initiative)
    context_dir.mkdir(parents=True, exist_ok=True)
    created: list[str] = []

    md_path = map_path(root, initiative)
    legacy_path = legacy_map_path(root, initiative)
    if not md_path.exists():
        if legacy_path.exists():
            md_path.write_text(legacy_path.read_text(encoding="utf-8"), encoding="utf-8")
        else:
            md_path.write_text(map_template(initiative, title, timestamp), encoding="utf-8")
        created.append("map.md")

    json_path = map_json_path(root, initiative)
    if json_path.exists():
        data = read_json(json_path)
        data.setdefault("schema_version", MAP_SCHEMA_VERSION)
        data.setdefault("initiative", initiative)
        data.setdefault("title", title)
        data.setdefault("map_path", parent_map_ref(initiative))
        data.setdefault("packages", [])
        orchestration = data.setdefault("orchestration", base_map_json(initiative, title, timestamp)["orchestration"])
        if isinstance(orchestration, dict):
            defaults = base_map_json(initiative, title, timestamp)["orchestration"]
            for key, value in defaults.items():
                orchestration.setdefault(key, value)
            if orchestration.get("strategy") == "ready-packages-only":
                orchestration["strategy"] = "autonomous-package-pipeline"
        data.setdefault("history", [])
        if status is not None:
            data["status"] = status
        else:
            data.setdefault("status", "draft")
        data["updated_at"] = timestamp
    else:
        data = base_map_json(initiative, title, timestamp)
        data["status"] = status
        created.append("map.json")
    write_json(json_path, data)

    assignments_path = context_dir / "agent-assignments.jsonl"
    if write_if_missing(assignments_path, ""):
        created.append("context/agent-assignments.jsonl")

    return {"initiative": initiative, "map": parent_map_ref(initiative), "map_json": f".arbor/maps/{initiative}/map.json", "created": created}


def ensure_map_workspace(root: Path, initiative: str, timestamp: str) -> dict[str, Any]:
    if map_path(root, initiative).exists():
        return create_map(root, initiative, initiative, timestamp, status=None)
    if legacy_map_path(root, initiative).exists():
        return create_map(root, initiative, initiative, timestamp, status=None)
    raise ArborError(f"Missing initiative map: {map_path(root, initiative)}")


def create_package(root: Path, name: str, mode: str, title: str | None, source_type: str, timestamp: str) -> dict[str, Any]:
    validate_name(name)
    if mode not in MODES:
        raise ArborError(f"Invalid mode '{mode}'. Expected one of: {', '.join(sorted(MODES))}.")
    if source_type not in {"new", "legacy-brainstorm", "ad-hoc", "map-split"}:
        raise ArborError("Invalid source type. Expected new, legacy-brainstorm, ad-hoc, or map-split.")

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
    placeholder_patterns = [
        r"<[^>\n]*(?:feature|package|initiative|deliverable|path|behavior|里程碑|任务|hours|title|source|why|domain|contract|blocker|next)[^>\n]*>",
        r"\bSlice [A-Z]:\s*$",
    ]
    return any(re.search(pattern, text, re.MULTILINE) for pattern in placeholder_patterns)


def validate_optional_string(value: Any, label: str, errors: list[str]) -> None:
    if value is not None and not isinstance(value, str):
        errors.append(f"{label} must be a string or null")


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


def validate_execution(data: dict[str, Any], task_ids: set[str], errors: list[str]) -> None:
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

    agents = execution.get("agents")
    if not isinstance(agents, list):
        errors.append("execution.agents must be an array")
    else:
        for index, agent in enumerate(agents):
            if not isinstance(agent, dict):
                errors.append(f"execution.agents[{index}] must be an object")
                continue
            for field in ["role", "name", "status", "at", "summary"]:
                if field not in agent:
                    errors.append(f"execution.agents[{index}] missing field: {field}")
            if agent.get("role") not in AGENT_RECORD_ROLES:
                errors.append(f"execution.agents[{index}] has invalid role: {agent.get('role')}")
            if agent.get("status") not in AGENT_RECORD_STATUSES:
                errors.append(f"execution.agents[{index}] has invalid status: {agent.get('status')}")
            for field in ["name", "at", "summary", "actor", "note"]:
                validate_optional_string(agent.get(field), f"execution.agents[{index}].{field}", errors)
            task_id = agent.get("task_id")
            if task_id is not None and task_id not in task_ids:
                errors.append(f"execution.agents[{index}] references unknown task_id: {task_id}")


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
        for field in CHILD_TASK_EXECUTION_FIELDS:
            if field in task:
                errors.append(f"Task {task_id} must not define {field}; execution boundary is package-level")
        dependencies[task_id] = depends_on

    validate_package_sizing(data, errors)
    validate_execution(data, task_ids, errors)

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


def sorted_tasks(data: dict[str, Any], states: set[str] | None = None) -> list[dict[str, Any]]:
    tasks = data.get("tasks", []) if isinstance(data.get("tasks"), list) else []
    if states is not None:
        tasks = [task for task in tasks if task.get("state") in states]
    return sorted(tasks, key=lambda task: task.get("id", ""))


def dependencies_satisfied(task: dict[str, Any], states_by_id: dict[str, str]) -> bool:
    return all(states_by_id.get(dep) in DEPENDENCY_COMPLETE_STATES for dep in task.get("depends_on", []))


def recalculate_package_state(data: dict[str, Any]) -> None:
    tasks = sorted_tasks(data)
    if not tasks:
        return
    states_by_id = {task.get("id"): task.get("state") for task in tasks if isinstance(task.get("id"), str)}

    for state, package_state, phase, skill, reason in [
        ("brainstorm_drift", "brainstorm_drift", "review", "brainstorm", "package PRD is stale or incorrect"),
        ("needs_rework", "needs_rework", "review", "impl", "review found rework required"),
        ("in_progress", "in_progress", "impl", "impl", "implementation in progress"),
        ("done", "impl_done", "impl", "review", "implementation reported done; semantic audit pending"),
        ("done_with_concerns", "impl_done", "impl", "review", "implementation reported done with concerns; semantic audit pending"),
        ("needs_context", "needs_context", "task", "task", "task-local context is missing or conflicting"),
        ("blocked", "blocked", data.get("current_phase", "task"), "user", "external blocker requires user action"),
    ]:
        matches = sorted_tasks(data, {state})
        if matches:
            task_id = matches[0].get("id")
            data["state"] = package_state
            data["current_phase"] = phase
            data["active_task"] = task_id if state == "in_progress" else None
            data["next_action"] = {"skill": skill, "task_id": task_id, "reason": reason}
            if package_state in {"impl_done", "reviewed"}:
                execution = ensure_execution(data)
                if execution.get("status") not in {"claimed", "worktree_ready", "pr_open", "merged"}:
                    execution["status"] = package_state
            return

    required_tasks = [task for task in tasks if task.get("state") != "skipped"]
    if required_tasks and all(task.get("state") in REVIEW_PASS_STATES for task in required_tasks):
        data["state"] = "reviewed"
        data["current_phase"] = "review"
        data["active_task"] = None
        data["next_action"] = {"skill": "none", "task_id": None, "reason": "all required package-local tasks passed review"}
        execution = ensure_execution(data)
        if execution.get("status") not in {"claimed", "worktree_ready", "pr_open", "merged"}:
            execution["status"] = "reviewed"
        return

    ready_tasks = [task for task in sorted_tasks(data, {"ready"}) if dependencies_satisfied(task, states_by_id)]
    if ready_tasks:
        task_id = ready_tasks[0].get("id")
        data["state"] = "ready"
        data["current_phase"] = "task"
        data["active_task"] = None
        data["next_action"] = {"skill": "impl", "task_id": task_id, "reason": "next package-local ready task"}
        return


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
        elif state in {"done", "done_with_concerns"}:
            task["last_impl_result"] = {
                "state": "DONE" if state == "done" else "DONE_WITH_CONCERNS",
                "at": timestamp,
                "summary": note,
                "acceptance": [],
                "concerns": [],
            }
        elif state == "needs_context":
            task["last_impl_result"] = {
                "state": "NEEDS_CONTEXT",
                "at": timestamp,
                "summary": note,
                "acceptance": [],
                "concerns": [],
            }
        elif state == "blocked":
            task["last_impl_result"] = {
                "state": "BLOCKED",
                "at": timestamp,
                "summary": note,
                "acceptance": [],
                "concerns": [],
            }
        elif state in {"approved", "approved_with_notes"}:
            task["last_review_result"] = {
                "state": "APPROVED" if state == "approved" else "APPROVED_WITH_NOTES",
                "at": timestamp,
                "summary": note,
                "evidence": [],
                "notes": [],
            }
        elif state == "needs_rework":
            task["last_review_result"] = {
                "state": "NEEDS_REWORK",
                "at": timestamp,
                "summary": note,
                "evidence": [],
                "notes": [],
            }
        elif state == "brainstorm_drift":
            task["last_review_result"] = {
                "state": "BRAINSTORM_DRIFT",
                "at": timestamp,
                "summary": note,
                "evidence": [],
                "notes": [],
            }
        elif state == "skipped":
            if data.get("active_task") == task_id:
                data["active_task"] = None
        recalculate_package_state(data)
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


def claim_package(root: Path, name: str, owner: str, actor: str, note: str, timestamp: str, force: bool, branch: str | None, base_branch: str | None, worktree: str | None, session: str | None) -> dict[str, Any]:
    pkg, data = load_package(root, name)
    execution = ensure_execution(data)
    current_owner = execution.get("owner")
    if current_owner and current_owner != owner and not force:
        raise ArborError(f"Package already claimed by {current_owner}. Use --force to override.")
    execution["status"] = "claimed"
    execution["owner"] = owner
    execution["claimed_at"] = timestamp
    execution["released_at"] = None
    execution["updated_at"] = timestamp
    execution["updated_by"] = actor
    execution["note"] = note
    if session:
        execution["session"] = session
    if branch:
        execution["branch"]["name"] = branch
    if base_branch:
        execution["branch"]["base"] = base_branch
    if worktree:
        execution["worktree"]["path"] = worktree
    data["updated_at"] = timestamp
    save_package(pkg, data)
    return data


def release_package(root: Path, name: str, owner: str | None, actor: str, note: str, timestamp: str, force: bool) -> dict[str, Any]:
    pkg, data = load_package(root, name)
    execution = ensure_execution(data)
    current_owner = execution.get("owner")
    if owner and current_owner and current_owner != owner and not force:
        raise ArborError(f"Package claimed by {current_owner}, not {owner}. Use --force to release.")
    execution["status"] = "unclaimed"
    execution["owner"] = None
    execution["released_at"] = timestamp
    execution["updated_at"] = timestamp
    execution["updated_by"] = actor
    execution["note"] = note
    data["updated_at"] = timestamp
    save_package(pkg, data)
    return data


def set_execution(root: Path, name: str, status: str | None, actor: str, note: str, timestamp: str, base_branch: str | None, branch: str | None, upstream: str | None, worktree: str | None, worktree_created_by: str | None) -> dict[str, Any]:
    pkg, data = load_package(root, name)
    execution = ensure_execution(data)
    if status:
        if status not in EXECUTION_STATUSES:
            raise ArborError(f"Invalid execution status '{status}'.")
        execution["status"] = status
    if base_branch:
        execution["branch"]["base"] = base_branch
    if branch:
        execution["branch"]["name"] = branch
    if upstream:
        execution["branch"]["upstream"] = upstream
    if worktree:
        execution["worktree"]["path"] = worktree
    if worktree_created_by:
        execution["worktree"]["created_by"] = worktree_created_by
    execution["updated_at"] = timestamp
    execution["updated_by"] = actor
    execution["note"] = note
    data["updated_at"] = timestamp
    save_package(pkg, data)
    return data


def set_pr(root: Path, name: str, actor: str, note: str, timestamp: str, url: str | None, number: int | None, state: str | None) -> dict[str, Any]:
    pkg, data = load_package(root, name)
    execution = ensure_execution(data)
    pr = execution.setdefault("pr", {"url": None, "number": None, "state": "none"})
    if url:
        pr["url"] = url
    if number is not None:
        pr["number"] = number
    if state:
        if state not in PR_STATES:
            raise ArborError(f"Invalid PR state '{state}'.")
        pr["state"] = state
        if state == "open":
            execution["status"] = "pr_open"
        elif state == "merged":
            execution["status"] = "merged"
    execution["updated_at"] = timestamp
    execution["updated_by"] = actor
    execution["note"] = note
    data["updated_at"] = timestamp
    save_package(pkg, data)
    return data


def record_agent(root: Path, name: str, role: str, agent_name: str, status: str, summary: str, actor: str, note: str, timestamp: str, task_id: str | None) -> dict[str, Any]:
    if role not in AGENT_RECORD_ROLES:
        raise ArborError(f"Invalid agent role '{role}'.")
    if status not in AGENT_RECORD_STATUSES:
        raise ArborError(f"Invalid agent status '{status}'.")
    pkg, data = load_package(root, name)
    if task_id:
        find_task(data, task_id)
    execution = ensure_execution(data)
    execution.setdefault("agents", []).append(
        {
            "role": role,
            "name": agent_name,
            "status": status,
            "task_id": task_id,
            "at": timestamp,
            "summary": summary,
            "actor": actor,
            "note": note,
        }
    )
    execution["updated_at"] = timestamp
    execution["updated_by"] = actor
    execution["note"] = note
    data["updated_at"] = timestamp
    save_package(pkg, data)
    return data


def infer_sizing_phase(data: dict[str, Any], actor: str, phase: str | None) -> str:
    if phase:
        if phase not in PHASES:
            raise ArborError(f"Invalid package sizing phase '{phase}'.")
        return phase
    if actor in {"brainstorm", "map", "task"}:
        return actor
    current_phase = data.get("current_phase")
    return current_phase if current_phase in PHASES else "brainstorm"


def parse_split_package_spec(raw: str) -> dict[str, Any]:
    parts = raw.split("::")
    if len(parts) != 4:
        raise ArborError("Split package spec must use format name::title::dep1,dep2::boundary_reason.")
    name, title, deps_raw, boundary_reason = [part.strip() for part in parts]
    validate_name(name)
    if not title:
        raise ArborError(f"Split package '{name}' requires a title.")
    if not boundary_reason:
        raise ArborError(f"Split package '{name}' requires a boundary reason.")
    depends_on = [item.strip() for item in deps_raw.split(",") if item.strip()]
    for dep in depends_on:
        validate_name(dep)
        if dep == name:
            raise ArborError(f"Split package '{name}' cannot depend on itself.")
    return {"name": name, "title": title, "depends_on_packages": depends_on, "boundary_reason": boundary_reason}


def ensure_same_or_empty(value: Any, expected: str, label: str, package_name: str) -> None:
    if value not in {None, expected}:
        raise ArborError(f"Package '{package_name}' already has {label}={value!r}; expected {expected!r}.")


def ensure_parent_map_same_or_legacy(value: Any, initiative: str, label: str, package_name: str) -> None:
    expected = parent_map_ref(initiative)
    legacy = legacy_parent_map_ref(initiative)
    if value not in {None, expected, legacy}:
        raise ArborError(f"Package '{package_name}' already has {label}={value!r}; expected {expected!r}.")


def package_map_entry(spec: dict[str, Any], timestamp: str) -> dict[str, Any]:
    name = spec["name"]
    return {
        "name": name,
        "title": spec["title"],
        "path": f".arbor/tasks/{name}",
        "materialized": True,
        "depends_on": spec["depends_on_packages"],
        "wave": spec.get("wave") or None,
        "boundary_reason": spec["boundary_reason"],
        "contract_inputs": [],
        "contract_outputs": [],
        "prd_status": "draft",
        "task_state": "planned",
        "execution_status": "unclaimed",
        "next_action": {"skill": "brainstorm", "task_id": None},
        "updated_at": timestamp,
    }


def upsert_map_packages(root: Path, initiative: str, specs: list[dict[str, Any]], actor: str, decision: str, timestamp: str) -> dict[str, Any]:
    workspace = create_map(root, initiative, initiative, timestamp, status="active")
    data = read_json(map_json_path(root, initiative))
    packages = data.get("packages")
    if not isinstance(packages, list):
        packages = []
    by_name: dict[str, dict[str, Any]] = {item.get("name"): item for item in packages if isinstance(item, dict) and isinstance(item.get("name"), str)}
    ordered_names = [item.get("name") for item in packages if isinstance(item, dict) and isinstance(item.get("name"), str)]
    for spec in specs:
        name = spec["name"]
        entry = by_name.get(name, {})
        entry.update(package_map_entry(spec, timestamp))
        by_name[name] = entry
        if name not in ordered_names:
            ordered_names.append(name)
    data["packages"] = [by_name[name] for name in ordered_names]
    data["updated_at"] = timestamp
    data.setdefault("history", []).append({"at": timestamp, "actor": actor, "event": "packages_materialized", "note": decision, "packages": [spec["name"] for spec in specs]})
    write_json(map_json_path(root, initiative), data)
    return workspace


def create_split_packages(root: Path, initiative: str, package_specs: list[str], actor: str, mode: str, decision: str, timestamp: str) -> dict[str, Any]:
    validate_name(initiative)
    if mode not in MODES:
        raise ArborError(f"Invalid mode '{mode}'.")
    if not decision:
        raise ArborError("create-split-packages requires a non-empty decision.")
    ensure_map_workspace(root, initiative, timestamp)

    specs = [parse_split_package_spec(raw) for raw in package_specs]
    seen: set[str] = set()
    spec_names = {spec["name"] for spec in specs}
    for spec in specs:
        name = spec["name"]
        if name == initiative:
            raise ArborError("Split package name must not equal the parent initiative name.")
        if name in seen:
            raise ArborError(f"Duplicate split package: {name}")
        seen.add(name)
        for dep in spec["depends_on_packages"]:
            if dep not in spec_names and not package_dir(root, dep).exists():
                raise ArborError(f"Split package '{name}' depends on unknown package '{dep}'.")

    parent_map = parent_map_ref(initiative)
    for spec in specs:
        name = spec["name"]
        pkg_path = package_dir(root, name)
        if (pkg_path / "task.json").exists():
            existing = read_json(pkg_path / "task.json")
            existing_prd = existing.get("prd") if isinstance(existing.get("prd"), dict) else {}
            existing_sizing = existing.get("package_sizing") if isinstance(existing.get("package_sizing"), dict) else {}
            ensure_same_or_empty(existing_prd.get("parent_initiative"), initiative, "prd.parent_initiative", name)
            ensure_parent_map_same_or_legacy(existing_prd.get("parent_map"), initiative, "prd.parent_map", name)
            ensure_same_or_empty(existing_sizing.get("parent_initiative"), initiative, "package_sizing.parent_initiative", name)
            ensure_parent_map_same_or_legacy(existing_sizing.get("parent_map"), initiative, "package_sizing.parent_map", name)
            existing_status = existing_sizing.get("status")
            if existing_status not in {None, "unchecked", "split_applied"}:
                raise ArborError(f"Package '{name}' already has incompatible package_sizing.status={existing_status!r}.")

    upsert_map_packages(root, initiative, specs, actor, decision, timestamp)
    materialized: list[dict[str, Any]] = []
    for spec in specs:
        name = spec["name"]
        result = create_package(root, name, mode, spec["title"], "map-split", timestamp)
        pkg, data = load_package(root, name)
        prd = data.setdefault("prd", {})
        prd["source_type"] = "map-split"
        prd["parent_map"] = parent_map
        prd["parent_initiative"] = initiative
        prd.setdefault("status", "draft")
        prd.setdefault("ready_for_task_at", None)
        old = data.get("package_sizing", {}).get("status") if isinstance(data.get("package_sizing"), dict) else None
        data["package_sizing"] = {
            "status": "split_applied",
            "decision": decision,
            "signals": ["materialized_from_map"],
            "recommended_packages": [],
            "parent_map": parent_map,
            "parent_initiative": initiative,
            "depends_on_packages": spec["depends_on_packages"],
            "boundary_reason": spec["boundary_reason"],
            "decided_at": timestamp,
            "decided_by": actor,
            "note": f"materialized from {parent_map}",
        }
        data["state"] = "planned"
        data["current_phase"] = "brainstorm"
        data["active_task"] = None
        data["next_action"] = {"skill": "brainstorm", "task_id": None, "reason": "map-split child package PRD draft"}
        data["updated_at"] = timestamp
        add_phase_history(data, timestamp, "map", None, old, "package_sizing:split_applied", actor, f"materialized from {parent_map}")
        save_package(pkg, data)
        materialized.append({"name": name, "path": f".arbor/tasks/{name}", "created": result["created"], "depends_on_packages": spec["depends_on_packages"]})

    sync_map_from_packages(root, initiative, timestamp)
    return {"initiative": initiative, "map": parent_map, "map_json": f".arbor/maps/{initiative}/map.json", "packages": materialized}


def read_package_summary(root: Path, name: str) -> dict[str, Any]:
    pkg = package_dir(root, name)
    if not (pkg / "task.json").exists():
        return {
            "name": name,
            "path": f".arbor/tasks/{name}",
            "exists": False,
            "validation": {"ok": False, "errors": ["package task.json missing"]},
        }
    data = read_json(pkg / "task.json")
    errors = validate_package(root, name)
    tasks = data.get("tasks", []) if isinstance(data.get("tasks"), list) else []
    execution = ensure_execution(data)
    prd = data.get("prd") if isinstance(data.get("prd"), dict) else {}
    sizing = data.get("package_sizing") if isinstance(data.get("package_sizing"), dict) else {}
    next_action = data.get("next_action") if isinstance(data.get("next_action"), dict) else {}
    return {
        "name": name,
        "title": data.get("title") or name,
        "path": f".arbor/tasks/{name}",
        "exists": True,
        "state": data.get("state"),
        "current_phase": data.get("current_phase"),
        "prd_status": prd.get("status"),
        "package_sizing": sizing.get("status"),
        "depends_on": sizing.get("depends_on_packages", []) if isinstance(sizing.get("depends_on_packages", []), list) else [],
        "parent_initiative": prd.get("parent_initiative") or sizing.get("parent_initiative"),
        "next_action": {"skill": next_action.get("skill"), "task_id": next_action.get("task_id"), "reason": next_action.get("reason")},
        "execution_status": execution.get("status"),
        "execution_owner": execution.get("owner"),
        "pr_state": execution.get("pr", {}).get("state") if isinstance(execution.get("pr"), dict) else None,
        "task_count": len(tasks),
        "ready_count": sum(1 for task in tasks if task.get("state") == "ready"),
        "blocked_count": sum(1 for task in tasks if task.get("state") in {"blocked", "needs_context"}),
        "validation": {"ok": not errors, "errors": errors},
    }


def map_package_names(root: Path, initiative: str, data: dict[str, Any]) -> list[str]:
    names: list[str] = []
    for entry in data.get("packages", []) if isinstance(data.get("packages"), list) else []:
        if isinstance(entry, dict) and isinstance(entry.get("name"), str) and entry["name"] not in names:
            names.append(entry["name"])
    root_dir = tasks_root(root)
    if root_dir.exists():
        for pkg in sorted(path for path in root_dir.iterdir() if path.is_dir()):
            task_path = pkg / "task.json"
            if not task_path.exists():
                continue
            try:
                task_data = read_json(task_path)
            except ArborError:
                continue
            prd = task_data.get("prd") if isinstance(task_data.get("prd"), dict) else {}
            sizing = task_data.get("package_sizing") if isinstance(task_data.get("package_sizing"), dict) else {}
            if initiative in {prd.get("parent_initiative"), sizing.get("parent_initiative")} and pkg.name not in names:
                names.append(pkg.name)
    return names


def sync_map_from_packages(root: Path, initiative: str, timestamp: str) -> dict[str, Any]:
    ensure_map_workspace(root, initiative, timestamp)
    json_path = map_json_path(root, initiative)
    data = read_json(json_path)
    existing_entries = data.get("packages", []) if isinstance(data.get("packages"), list) else []
    by_name: dict[str, dict[str, Any]] = {entry.get("name"): entry for entry in existing_entries if isinstance(entry, dict) and isinstance(entry.get("name"), str)}
    names = map_package_names(root, initiative, data)
    synced: list[dict[str, Any]] = []
    for name in names:
        entry = by_name.get(name, {"name": name, "path": f".arbor/tasks/{name}"})
        summary = read_package_summary(root, name)
        if summary.get("exists"):
            entry["title"] = summary.get("title") or entry.get("title") or name
            entry["path"] = summary.get("path")
            entry["materialized"] = True
            entry["depends_on"] = summary.get("depends_on", entry.get("depends_on", []))
            entry["prd_status"] = summary.get("prd_status")
            entry["task_state"] = summary.get("state")
            entry["current_phase"] = summary.get("current_phase")
            entry["execution_status"] = summary.get("execution_status")
            entry["execution_owner"] = summary.get("execution_owner")
            entry["next_action"] = summary.get("next_action")
            entry["task_count"] = summary.get("task_count")
            entry["ready_count"] = summary.get("ready_count")
            entry["blocked_count"] = summary.get("blocked_count")
            entry["validation"] = summary.get("validation")
        else:
            entry.setdefault("path", f".arbor/tasks/{name}")
            entry["materialized"] = False
            entry["validation"] = summary.get("validation")
        entry.setdefault("wave", None)
        entry.setdefault("boundary_reason", None)
        entry.setdefault("contract_inputs", [])
        entry.setdefault("contract_outputs", [])
        entry["updated_at"] = timestamp
        synced.append(entry)
    data["packages"] = synced
    data["updated_at"] = timestamp
    write_json(json_path, data)
    return data


def package_dependency_complete(summary: dict[str, Any]) -> bool:
    return summary.get("state") in {"reviewed", "completed"} or summary.get("execution_status") in {"reviewed", "merged"} or summary.get("pr_state") == "merged"


def package_active(summary: dict[str, Any]) -> bool:
    return summary.get("state") == "in_progress" or summary.get("execution_status") in {"claimed", "worktree_ready", "in_progress", "pr_open"}


def package_assignable(summary: dict[str, Any]) -> bool:
    if not summary.get("exists"):
        return False
    if not summary.get("validation", {}).get("ok"):
        return False
    if package_dependency_complete(summary) or package_active(summary):
        return False
    if summary.get("state") in {"blocked", "needs_context", "superseded"}:
        return False
    next_action = summary.get("next_action") if isinstance(summary.get("next_action"), dict) else {}
    return next_action.get("skill") in {"brainstorm", "task", "impl", "review"}


def wave_sort_key(entry: dict[str, Any]) -> tuple[int, str, str]:
    wave = entry.get("wave")
    if isinstance(wave, str):
        match = re.search(r"\d+", wave)
        if match:
            return (int(match.group()), wave, entry.get("name", ""))
    return (999, str(wave or ""), entry.get("name", ""))


def map_check(root: Path, initiative: str, timestamp: str) -> dict[str, Any]:
    data = sync_map_from_packages(root, initiative, timestamp)
    summaries = {entry["name"]: read_package_summary(root, entry["name"]) for entry in data.get("packages", []) if isinstance(entry, dict) and isinstance(entry.get("name"), str)}
    package_entries = {entry["name"]: entry for entry in data.get("packages", []) if isinstance(entry, dict) and isinstance(entry.get("name"), str)}
    ready: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    active: list[dict[str, Any]] = []
    complete: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []

    for name in sorted(summaries, key=lambda item: wave_sort_key(package_entries.get(item, {"name": item}))):
        summary = summaries[name]
        entry = package_entries.get(name, {"name": name})
        deps = entry.get("depends_on", summary.get("depends_on", []))
        dependency_blockers: list[dict[str, Any]] = []
        for dep in deps if isinstance(deps, list) else []:
            dep_summary = summaries.get(dep) if dep in summaries else read_package_summary(root, dep)
            if not package_dependency_complete(dep_summary):
                dependency_blockers.append({"name": dep, "state": dep_summary.get("state"), "exists": dep_summary.get("exists"), "execution_status": dep_summary.get("execution_status")})

        item = {
            "name": name,
            "path": summary.get("path"),
            "wave": entry.get("wave"),
            "state": summary.get("state"),
            "prd_status": summary.get("prd_status"),
            "execution_status": summary.get("execution_status"),
            "next_action": summary.get("next_action"),
            "depends_on": deps if isinstance(deps, list) else [],
            "validation": summary.get("validation"),
        }
        if not summary.get("exists"):
            item["reason"] = "package stub missing"
            missing.append(item)
        elif package_dependency_complete(summary):
            complete.append(item)
        elif package_active(summary):
            item["reason"] = "package already claimed or in progress"
            active.append(item)
        elif dependency_blockers:
            item["blocked_by"] = dependency_blockers
            blocked.append(item)
        elif not summary.get("validation", {}).get("ok"):
            item["reason"] = "package validation failed"
            blocked.append(item)
        elif summary.get("state") in {"blocked", "needs_context", "superseded"}:
            item["reason"] = f"package state is {summary.get('state')}"
            blocked.append(item)
        elif package_assignable(summary):
            ready.append(item)
        else:
            item["reason"] = "no assignable next action"
            blocked.append(item)

    return {
        "initiative": initiative,
        "map": parent_map_ref(initiative),
        "map_json": f".arbor/maps/{initiative}/map.json",
        "ready": ready,
        "blocked": blocked,
        "active": active,
        "complete": complete,
        "missing": missing,
    }


def assignment_context(root: Path, initiative: str, item: dict[str, Any], check: dict[str, Any]) -> dict[str, Any]:
    name = item["name"]
    summary = read_package_summary(root, name)
    deps = item.get("depends_on", []) if isinstance(item.get("depends_on"), list) else []
    dependency_summaries = [read_package_summary(root, dep) for dep in deps]
    return {
        "initiative": initiative,
        "package": name,
        "package_path": f".arbor/tasks/{name}",
        "next_action": item.get("next_action"),
        "context_files": [
            parent_map_ref(initiative),
            f".arbor/maps/{initiative}/map.json",
            f".arbor/tasks/{name}/prd.md",
            f".arbor/tasks/{name}/task.md",
            f".arbor/tasks/{name}/task.json",
            f".arbor/tasks/{name}/context/impl.jsonl",
            f".arbor/tasks/{name}/context/sources.jsonl",
        ],
        "dependency_summaries": [
            {
                "name": dep.get("name"),
                "state": dep.get("state"),
                "prd_status": dep.get("prd_status"),
                "execution_status": dep.get("execution_status"),
                "path": dep.get("path"),
            }
            for dep in dependency_summaries
        ],
        "worker_prompt": (
            f"Act as a sdd-kit package dispatch worker for package '{name}'. "
            f"Read {parent_map_ref(initiative)} and .arbor/maps/{initiative}/map.json for initiative context, "
            f"then work only inside .arbor/tasks/{name}/ as the executable package boundary. "
            f"Start from task.json next_action={summary.get('next_action', {}).get('skill')} and keep advancing brainstorm/task/impl/review "
            "until the package is reviewed/completed, blocked, needs_context, or needs a user decision. "
            "Do not start downstream packages, modify sibling package task.json files, create PRs, push, deploy, or take destructive actions."
        ),
    }


def map_plan_agents(root: Path, initiative: str, max_parallel: int, actor: str, timestamp: str) -> dict[str, Any]:
    if max_parallel < 1:
        raise ArborError("--max-parallel must be at least 1.")
    if max_parallel > 4:
        raise ArborError("--max-parallel must be 4 or less; keep orchestration bounded.")
    check = map_check(root, initiative, timestamp)
    assignments = []
    for item in check["ready"][:max_parallel]:
        assignments.append(assignment_context(root, initiative, item, check))
    plan = {
        "at": timestamp,
        "actor": actor,
        "initiative": initiative,
        "max_parallel": max_parallel,
        "strategy": "autonomous-package-pipeline",
        "assignments": assignments,
        "blocked_count": len(check["blocked"]),
        "active_count": len(check["active"]),
        "complete_count": len(check["complete"]),
    }
    append_jsonl(map_context_dir(root, initiative) / "agent-assignments.jsonl", plan)
    return plan


def set_package_sizing(root: Path, name: str, status: str, actor: str, note: str, timestamp: str, decision: str | None, signals: list[str], recommended_packages: list[str], phase: str | None = None) -> dict[str, Any]:
    if status not in PACKAGE_SIZING_STATUSES:
        raise ArborError(f"Invalid package sizing status '{status}'.")
    pkg, data = load_package(root, name)
    sizing_phase = infer_sizing_phase(data, actor, phase)
    recommended: list[dict[str, Any]] = []
    for raw in recommended_packages:
        parts = raw.split(":", 2)
        package_name = parts[0].strip()
        if not NAME_RE.match(package_name):
            raise ArborError(f"Invalid recommended package name '{package_name}'.")
        depends_on = [item.strip() for item in parts[1].split(",") if item.strip()] if len(parts) >= 2 and parts[1].strip() else []
        for dep in depends_on:
            if not NAME_RE.match(dep):
                raise ArborError(f"Invalid recommended package dependency '{dep}'.")
        reason = parts[2].strip() if len(parts) == 3 else ""
        recommended.append({"name": package_name, "depends_on": depends_on, "reason": reason})
    old = data.get("package_sizing", {}).get("status") if isinstance(data.get("package_sizing"), dict) else None
    data["package_sizing"] = {
        "status": status,
        "decision": decision,
        "signals": signals,
        "recommended_packages": recommended,
        "decided_at": timestamp,
        "decided_by": actor,
        "note": note,
    }
    if status == "split_recommended":
        data["current_phase"] = "map"
        data["next_action"] = {"skill": "map", "task_id": None, "reason": "package graph required before task decomposition"}
    data["updated_at"] = timestamp
    add_phase_history(data, timestamp, sizing_phase, None, old, f"package_sizing:{status}", actor, note)
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
    if status == "ready-for-task":
        sizing = data.get("package_sizing") if isinstance(data.get("package_sizing"), dict) else {}
        sizing_status = sizing.get("status")
        if sizing_status == "unchecked":
            raise ArborError("Cannot mark PRD ready-for-task before brainstorm/map records package sizing as fits_package or split_applied.")
        if sizing_status == "split_recommended":
            raise ArborError("Cannot mark PRD ready-for-task while package sizing recommends a map/package graph split.")
        if sizing_status not in {"fits_package", "split_applied"}:
            raise ArborError("Cannot mark PRD ready-for-task without resolved package sizing: expected fits_package or split_applied.")
    prd["status"] = status
    if status == "ready-for-task":
        prd["ready_for_task_at"] = timestamp
        data["state"] = "ready"
        data["current_phase"] = "task"
        data["next_action"] = {"skill": "task", "task_id": None, "reason": "executable package PRD ready for task decomposition"}
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
    recalculate_package_state(data)
    if not data.get("tasks"):
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
    sizing = data.get("package_sizing") if isinstance(data.get("package_sizing"), dict) else {}
    if sizing.get("status") == "unchecked":
        raise ArborError("Package boundary sizing must be resolved by brainstorm/map before adding T-xxx tasks: expected fits_package or split_applied.")
    if sizing.get("status") == "split_recommended":
        raise ArborError("Package sizing routes this input to map; create the package graph and child package PRDs before adding package-local T-xxx tasks.")
    if sizing.get("status") not in {"fits_package", "split_applied"}:
        raise ArborError("Cannot add T-xxx tasks without resolved package sizing: expected fits_package or split_applied.")
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
    recalculate_package_state(data)
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
        execution = data.get("execution") if isinstance(data.get("execution"), dict) else {}
        branch = execution.get("branch") if isinstance(execution.get("branch"), dict) else {}
        worktree = execution.get("worktree") if isinstance(execution.get("worktree"), dict) else {}
        pr = execution.get("pr") if isinstance(execution.get("pr"), dict) else {}
        sizing = data.get("package_sizing") if isinstance(data.get("package_sizing"), dict) else {}
        result.append(
            {
                "name": pkg.name,
                "state": data.get("state"),
                "current_phase": data.get("current_phase"),
                "package_sizing": sizing.get("status"),
                "active_task": data.get("active_task"),
                "next_action": data.get("next_action"),
                "execution_status": execution.get("status"),
                "execution_owner": execution.get("owner"),
                "branch": branch.get("name"),
                "worktree": worktree.get("path"),
                "pr": pr.get("url") or pr.get("number"),
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
        "execution": data.get("execution"),
        "package_sizing": data.get("package_sizing"),
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
            f"{item['name']}\tstate={item.get('state')}\tphase={item.get('current_phase')}\tsizing={item.get('package_sizing')}\t"
            f"active={item.get('active_task')}\tnext={next_action.get('skill')}:{next_action.get('task_id')}\t"
            f"exec={item.get('execution_status')} owner={item.get('execution_owner')} branch={item.get('branch')} pr={item.get('pr')}\t"
            f"tasks={item.get('task_count')} ready={item.get('ready_count')} blocked={item.get('blocked_count')}"
        )


def print_human_show(data: dict[str, Any]) -> None:
    print(f"Package: {data['name']}")
    print(f"Path: {data['package']}")
    print(f"State: {data.get('state')}")
    print(f"Phase: {data.get('current_phase')}")
    print(f"Active task: {data.get('active_task')}")
    print(f"Next action: {data.get('next_action')}")
    print(f"Package sizing: {data.get('package_sizing')}")
    print(f"Execution: {data.get('execution')}")
    print(f"PRD: {data.get('prd')}")
    print(f"Validation: {'ok' if data['validation']['ok'] else 'failed'}")
    for error in data["validation"]["errors"]:
        print(f"  - {error}")
    if data.get("tasks"):
        print("Tasks:")
        for task in data["tasks"]:
            print(f"  - {task.get('id')} {task.get('state')} {task.get('title')}")


def print_human_map_check(data: dict[str, Any]) -> None:
    print(f"Initiative: {data['initiative']}")
    print(f"Map: {data['map']}")
    for label in ["ready", "active", "blocked", "missing", "complete"]:
        print(f"{label.capitalize()}:")
        items = data.get(label, [])
        if not items:
            print("  - none")
            continue
        for item in items:
            detail = item.get("reason") or item.get("next_action", {}).get("skill") or item.get("state")
            print(f"  - {item.get('name')} wave={item.get('wave')} state={item.get('state')} exec={item.get('execution_status')} detail={detail}")
            for blocker in item.get("blocked_by", []) if isinstance(item.get("blocked_by"), list) else []:
                print(f"      blocked_by {blocker.get('name')} state={blocker.get('state')} exec={blocker.get('execution_status')}")


def print_human_agent_plan(data: dict[str, Any]) -> None:
    print(f"Initiative: {data['initiative']}")
    print(f"Strategy: {data['strategy']} max_parallel={data['max_parallel']}")
    print("Mode: autonomous package pipeline; explicit stage skills are the manual review-gated path")
    if not data.get("assignments"):
        print("Assignments: none")
        return
    print("Assignments:")
    for item in data["assignments"]:
        print(f"  - {item['package']} next={item.get('next_action')}")
        print(f"    context: {', '.join(item.get('context_files', []))}")
        print(f"    prompt: {item.get('worker_prompt')}")


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
    create.add_argument("--source-type", choices=["new", "legacy-brainstorm", "ad-hoc", "map-split"], default="new")
    create.add_argument("--json", dest="json_output", action="store_true", help="Emit JSON output.")

    create_map_parser = sub.add_parser("create-map", help="Create an initiative map workspace with map.md and map.json.")
    create_map_parser.add_argument("initiative")
    create_map_parser.add_argument("--title")
    create_map_parser.add_argument("--status", choices=["draft", "active", "ready", "closed", "superseded"], default="draft")
    create_map_parser.add_argument("--json", dest="json_output", action="store_true", help="Emit JSON output.")

    split = sub.add_parser("create-split-packages", help="Materialize child task package stubs from an initiative map.")
    split.add_argument("initiative")
    split.add_argument("--package", action="append", required=True, help="name::title::dep1,dep2::boundary_reason")
    split.add_argument("--mode", choices=sorted(MODES), default="strict-atomic")
    split.add_argument("--decision", required=True)
    split.add_argument("--actor", default="map")
    split.add_argument("--json", dest="json_output", action="store_true", help="Emit JSON output.")

    map_check_parser = sub.add_parser("map-check", help="Check package readiness and blockers for an initiative map.")
    map_check_parser.add_argument("initiative")
    map_check_parser.add_argument("--json", dest="json_output", action="store_true", help="Emit JSON output.")

    map_plan_agents_parser = sub.add_parser("map-plan-agents", help="Create autonomous package pipeline worker assignment/context plan.")
    map_plan_agents_parser.add_argument("initiative")
    map_plan_agents_parser.add_argument("--max-parallel", type=int, default=2)
    map_plan_agents_parser.add_argument("--actor", default="map")
    map_plan_agents_parser.add_argument("--json", dest="json_output", action="store_true", help="Emit JSON output.")

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

    set_sizing = sub.add_parser("set-package-sizing", help="Record package boundary sizing from brainstorm/map; task uses it as a guard.")
    set_sizing.add_argument("name")
    set_sizing.add_argument("--status", required=True, choices=sorted(PACKAGE_SIZING_STATUSES))
    set_sizing.add_argument("--decision")
    set_sizing.add_argument("--signal", action="append", default=[])
    set_sizing.add_argument("--recommended-package", action="append", default=[], help="name[:dep1,dep2[:reason]]")
    set_sizing.add_argument("--phase", choices=sorted(PHASES), help="Lifecycle phase that made the boundary decision; inferred from actor when omitted.")
    set_sizing.add_argument("--actor", required=True)
    set_sizing.add_argument("--note", default="")

    freeze = sub.add_parser("freeze-definition", help="Mark task.md as frozen and ready for implementation.")
    freeze.add_argument("name")
    freeze.add_argument("--actor", required=True)
    freeze.add_argument("--note", default="")

    claim = sub.add_parser("claim-package", help="Record a package-level execution claim.")
    claim.add_argument("name")
    claim.add_argument("--owner", required=True)
    claim.add_argument("--branch")
    claim.add_argument("--base-branch")
    claim.add_argument("--worktree")
    claim.add_argument("--session")
    claim.add_argument("--force", action="store_true")
    claim.add_argument("--actor", default="arbor")
    claim.add_argument("--note", default="")

    release = sub.add_parser("release-package", help="Release a package-level execution claim.")
    release.add_argument("name")
    release.add_argument("--owner")
    release.add_argument("--force", action="store_true")
    release.add_argument("--actor", default="arbor")
    release.add_argument("--note", default="")

    set_execution_parser = sub.add_parser("set-execution", help="Record package-level branch/worktree execution metadata.")
    set_execution_parser.add_argument("name")
    set_execution_parser.add_argument("--status", choices=sorted(EXECUTION_STATUSES))
    set_execution_parser.add_argument("--base-branch")
    set_execution_parser.add_argument("--branch")
    set_execution_parser.add_argument("--upstream")
    set_execution_parser.add_argument("--worktree")
    set_execution_parser.add_argument("--worktree-created-by")
    set_execution_parser.add_argument("--actor", default="arbor")
    set_execution_parser.add_argument("--note", default="")

    set_pr_parser = sub.add_parser("set-pr", help="Record package-level PR metadata.")
    set_pr_parser.add_argument("name")
    set_pr_parser.add_argument("--url")
    set_pr_parser.add_argument("--number", type=int)
    set_pr_parser.add_argument("--state", choices=sorted(PR_STATES))
    set_pr_parser.add_argument("--actor", default="arbor")
    set_pr_parser.add_argument("--note", default="")

    record_agent_parser = sub.add_parser("record-agent", help="Record explicit external agent validation metadata.")
    record_agent_parser.add_argument("name")
    record_agent_parser.add_argument("--role", required=True, choices=sorted(AGENT_RECORD_ROLES))
    record_agent_parser.add_argument("--agent", required=True)
    record_agent_parser.add_argument("--status", required=True, choices=sorted(AGENT_RECORD_STATUSES))
    record_agent_parser.add_argument("--task")
    record_agent_parser.add_argument("--summary", required=True)
    record_agent_parser.add_argument("--actor", default="arbor")
    record_agent_parser.add_argument("--note", default="")

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

        if args.command == "create-map":
            result = create_map(root, args.initiative, args.title, timestamp, args.status)
            if json_output:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(f"Initiative: {result['initiative']}")
                print(f"Map: {result['map']}")
                if result["created"]:
                    print("Created: " + ", ".join(result["created"]))
                else:
                    print("Map already existed; no files overwritten.")
            return 0

        if args.command == "create-split-packages":
            result = create_split_packages(root, args.initiative, args.package, args.actor, args.mode, args.decision, timestamp)
            if json_output:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(f"Initiative: {result['initiative']}")
                print(f"Map: {result['map']}")
                for item in result["packages"]:
                    created = ", ".join(item["created"]) if item["created"] else "already existed"
                    print(f"  - {item['name']}: {created}")
            return 0

        if args.command == "map-check":
            result = map_check(root, args.initiative, timestamp)
            if json_output:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print_human_map_check(result)
            return 0

        if args.command == "map-plan-agents":
            result = map_plan_agents(root, args.initiative, args.max_parallel, args.actor, timestamp)
            if json_output:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print_human_agent_plan(result)
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

        if args.command == "set-package-sizing":
            set_package_sizing(root, args.name, args.status, args.actor, args.note, timestamp, args.decision, args.signal, args.recommended_package, args.phase)
            print("ok")
            return 0

        if args.command == "freeze-definition":
            freeze_definition(root, args.name, args.actor, args.note, timestamp)
            print("ok")
            return 0

        if args.command == "claim-package":
            claim_package(root, args.name, args.owner, args.actor, args.note, timestamp, args.force, args.branch, args.base_branch, args.worktree, args.session)
            print("ok")
            return 0

        if args.command == "release-package":
            release_package(root, args.name, args.owner, args.actor, args.note, timestamp, args.force)
            print("ok")
            return 0

        if args.command == "set-execution":
            set_execution(root, args.name, args.status, args.actor, args.note, timestamp, args.base_branch, args.branch, args.upstream, args.worktree, args.worktree_created_by)
            print("ok")
            return 0

        if args.command == "set-pr":
            set_pr(root, args.name, args.actor, args.note, timestamp, args.url, args.number, args.state)
            print("ok")
            return 0

        if args.command == "record-agent":
            record_agent(root, args.name, args.role, args.agent, args.status, args.summary, args.actor, args.note, timestamp, args.task)
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
