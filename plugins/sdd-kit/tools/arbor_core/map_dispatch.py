from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from .errors import ArborError
from .fs import *
from .schema import *
from .map_policy import normalize_string_list
from .map_readiness import map_check
from .map_runtime import append_parallel_runtime_event
from .map_sync import read_package_summary


def team_name_for_initiative(initiative: str) -> str:
    validate_name(initiative)
    return f"arbor-{initiative}"


def worker_name_for_package(name: str) -> str:
    validate_name(name)
    return f"pipeline-{name}"


def integration_worker_name_for_package(name: str) -> str:
    validate_name(name)
    return f"integration-{name}"


def package_branch_name(initiative: str, name: str) -> str:
    validate_name(initiative)
    validate_name(name)
    return f"arbor/{initiative}/{name}"


def default_worktree_root_ref(root: Path) -> str:
    project_name = root.resolve().name or "project"
    return f"../arbor-worktrees/{project_name}"


def normalize_worktree_root_ref(root: Path, worktree_root_ref: str | None) -> str:
    if worktree_root_ref is None or not worktree_root_ref.strip():
        return default_worktree_root_ref(root)
    value = worktree_root_ref.strip().rstrip("/")
    if not value:
        return default_worktree_root_ref(root)
    if value.startswith("~") or Path(value).is_absolute():
        raise ArborError("--worktree-root must be a portable project-root-relative ref, e.g. ../arbor-worktrees/<project>; absolute and home paths are runtime-only.")
    return value


def package_worktree_ref(root: Path, initiative: str, name: str, worktree_root_ref: str | None = None) -> str:
    validate_name(initiative)
    validate_name(name)
    base = normalize_worktree_root_ref(root, worktree_root_ref)
    return f"{base}/{initiative}/{name}"


def resolve_worktree_ref(root: Path, worktree_ref: str) -> Path:
    path = Path(worktree_ref)
    if path.is_absolute():
        return path.resolve()
    return (root / path).resolve()


def worker_dispatch_path(name: str) -> str:
    validate_name(name)
    return f".arbor/tasks/{name}/context/worker-dispatch.md"


def build_worker_dispatch_markdown(initiative: str, name: str, summary: dict[str, Any], deps: list[dict[str, Any]], assignment: dict[str, Any]) -> str:
    dependency_lines = "\n".join(
        f"- {dep.get('name')}: state={dep.get('state')} prd={dep.get('prd_status')} execution={dep.get('execution_status')} checkpoint={dep.get('latest_checkpoint')} lead_checkpoint={dep.get('latest_lead_checkpoint')} path={dep.get('path')}"
        for dep in deps
    ) or "- 无"
    context_lines = "\n".join(f"- `{path}`" for path in assignment["context_files"])
    next_action = summary.get("next_action") if isinstance(summary.get("next_action"), dict) else {}
    scope = assignment.get("modification_scope") if isinstance(assignment.get("modification_scope"), dict) else {}
    owned_paths = "\n".join(f"- `{path}`" for path in normalize_string_list(scope.get("owned_paths"))) or "- 默认按 PRD/task 的 package-local scope；除非 map 声明了更窄 owned_paths"
    shared_paths = "\n".join(f"- `{path}`" for path in normalize_string_list(scope.get("shared_paths"))) or "- 未声明"
    contract_inputs = "\n".join(f"- {item}" for item in normalize_string_list(assignment.get("contract_inputs"))) or "- 未声明"
    contract_outputs = "\n".join(f"- {item}" for item in normalize_string_list(assignment.get("contract_outputs"))) or "- 未声明"
    contract_request_lines = "\n".join(
        f"- {item.get('id')}: {item.get('consumer')} -> {item.get('producer')} status={item.get('status')} request={item.get('request')}"
        for item in assignment.get("open_contract_requests", [])
        if isinstance(item, dict)
    ) or "- 无"
    stop_line = f"- 停在进入 `{assignment['stop_before']}` 之前" if assignment.get("stop_before") else "- Stop before: 无"
    return f"""# Worker dispatch: {name}

使用语言：中文。

- Initiative: `{initiative}`
- Assignment ID: `{assignment['assignment_id']}`
- Dispatch round: `{assignment['round_id']}`
- Team runtime: `{assignment['team_name']}`
- Worker: `{assignment['worker_name']}`
- Package: `{name}`
- Workflow package path: `.arbor/tasks/{name}/`
- Assignment kind: `{assignment['assignment_kind']}`
- 允许推进到: `{assignment['allowed_until']}`
{stop_line}
- Dependency gate: `{assignment['dependency_gate']}`
- Branch: `{assignment['branch']}`
- Worktree ref: `{assignment['worktree_ref']}`
- Runtime resolved worktree path: `{assignment['resolved_worktree_path']}`
- Source repo root: `{assignment['source_repo_root']}`
- 当前阶段: `{summary.get('current_phase')}`
- 下一步: `{next_action.get('skill')}` task `{next_action.get('task_id')}` — {next_action.get('reason')}

## Worktree entry gate

Team teammate spawn-time `isolation=worktree` is not trusted. Runtime must start from source repo root `{assignment['source_repo_root']}` or another registered worktree of the same git repo; `EnterWorktree(path=...)` cannot enter an existing worktree from a non-git directory. Before any `Read` / `Edit` / `Write` / `Bash` / `NotebookEdit` or product/package action:

1. If current cwd is not inside this git repo, report `BLOCKER blocker: wrong_workspace` immediately; do not try to read or edit files.
2. Call `EnterWorktree(path="{assignment['resolved_worktree_path']}")`.
3. Verify `pwd`, `git rev-parse --show-toplevel`, and `git branch --show-current` match this package worktree and branch `{assignment['branch']}`.
4. Report `WORKTREE_READY` with `assignment_id`, `package`, `worktree_path`, and `branch`.
5. If any check fails, do not edit anything; report `BLOCKER` with `blocker: wrong_workspace`.

Portable worktree ref: `{assignment['worktree_ref']}`. Runtime resolved path is local to this machine and must not be treated as durable cross-device state.

## 必读上下文

{context_lines}

## 依赖摘要

{dependency_lines}

## 修改范围

- 概要: {scope.get('summary')}
- Integration role: `{scope.get('integration_role', 'package')}`
- 原因: {scope.get('reason')}

Owned paths:
{owned_paths}

Shared / integration-sensitive paths:
{shared_paths}

## 稳定契约

本 package 依赖的输入:
{contract_inputs}

本 package 承诺的输出:
{contract_outputs}

与本 package 相关的开放 contract requests:
{contract_request_lines}

如果本 package 需要 producer package 变更:
1. 同时消息 producer worker 和 lead。
2. 在缺失行为补齐前暂停本 package 的实现。
3. 请 lead 在 `map.json.contract_requests` 中记录 contract request。
4. 只有 lead 报告 mainline checkpoint/base 已更新后才继续。

## 主干同步边界

- 只依赖 mainline-visible facts：completed/merged packages 或 `lead-integration` / `contract-update` checkpoints。
- 不读取、不合并、不复制 sibling branches/worktrees。
- 只有 `reviewed`、但没有 lead checkpoint 的 producer，不是稳定依赖。

## 集成边界

- 除非 owned_paths 明确包含，package worker 不拥有 shared center files、global wiring、DI、routes、migration ordering、repo-wide config 或 E2E assembly。
- Shared/global assembly 属于 `lead_serial` serial integration worker lane；main session lead 只协调、审查和 checkpoint，不能直接实现 product/package changes。
- 如果实现需要修改 owned_paths 之外的 shared/global 内容，停止并报告 boundary drift。

## Artifact handoff

Worker 完成后报告 changed artifacts；lead 用下面的 helper 回收 package artifacts，不要求 worker 生成 patch：

```text
sdd-arbor import-package-artifacts {name} --from-worktree {assignment['worktree_ref']}
```

该 helper 默认同步 `prd.md`、`task.md`、`review.md`、`context/*.jsonl`，不会覆盖 `task.json`；package lifecycle/control state 继续由 lead 用 `release-package` / `set-status` / `record-checkpoint` 等 helper 更新。

## Team 协作

- 用 `TaskUpdate` 维护 shared Team task runtime status。
- 用 `SendMessage` 向 lead 报告 start、completion、blockers 和 contract questions。
- 可向 producer/consumer package workers 询问 contract 问题。
- Team messages 只协调 runtime work；durable decisions 必须落在 `.arbor` state、amendments、contract requests 或 git checkpoints。

## Structured worker reports

Every report starts with exactly one block label and includes `assignment_id`.

```text
WORKTREE_READY
assignment_id: {assignment['assignment_id']}
package: {name}
worktree_path: {assignment['resolved_worktree_path']}
branch: {assignment['branch']}
```

```text
WORKER_DONE
assignment_id: {assignment['assignment_id']}
package: {name}
summary: <what changed>
changed_artifacts: <prd.md, task.md, review.md, context/... or none>
control_state_request: <release-package | set-status | record-checkpoint | none>
review_state: <not_started | ready_for_review | reviewed>
needs_lead_checkpoint: <yes | no>
```

```text
CONTRACT_REQUEST
assignment_id: {assignment['assignment_id']}
consumer: <consumer package>
producer: <producer package>
request: <stable output/capability needed>
reason: <why current package is blocked>
blocked_until: contract-update checkpoint
```

```text
WAITING_INPUT
assignment_id: {assignment['assignment_id']}
package: {name}
waiting_for: <lead | user | producer | permission | context>
reason: <why progress stopped>
safe_next_action: <what the lead should do next>
```

```text
BLOCKER
assignment_id: {assignment['assignment_id']}
package: {name}
blocker: <wrong_workspace | validation | dependency | boundary | acceptance | external_side_effect>
reason: <specific blocker>
```

```text
READY_FOR_INTEGRATION
assignment_id: {assignment['assignment_id']}
package: {name}
checkpoint_needed: <lead-integration | contract-update>
summary: <what the lead should inspect/integrate>
```

```text
SHUTDOWN_ACK
assignment_id: {assignment['assignment_id']}
package: {name}
status: <stopped | already_idle>
```

## Worker contract

1. The main Claude session is the lead/orchestrator; this Team is only the runtime worker pool and shared task list.
2. First enter and verify the package worktree; do not trust Team spawn-time cwd/isolation, and do not touch files before `WORKTREE_READY`.
3. Run as worker teammate in the package worktree, not in the lead/orchestrator worktree.
4. Own only the declared modification scope; do not mutate sibling package state or patch producer internals.
5. Advance `task.json.next_action` only up to the assignment limit. If `stop_before` is set, stop and report before entering that phase.
6. For clear package-local drift, use forward-only amendment: append AMD-xxx, append linked T-xxx, then continue within the assignment limit.
7. Do not create PRs, push, deploy, delete data, or perform destructive actions unless the user explicitly authorizes that action.
8. Stop and report to the lead on ambiguity, package boundary drift, missing dependency contract, failing/unavailable acceptance, or unsafe external side effects.
"""


def write_worker_dispatch_packet(root: Path, initiative: str, name: str, summary: dict[str, Any], deps: list[dict[str, Any]], assignment: dict[str, Any]) -> str:
    path = root / worker_dispatch_path(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_worker_dispatch_markdown(initiative, name, summary, deps, assignment), encoding="utf-8")
    return worker_dispatch_path(name)


def assignment_context(root: Path, initiative: str, item: dict[str, Any], check: dict[str, Any], round_id: str, worktree_root_ref: str | None = None) -> dict[str, Any]:
    name = item["name"]
    summary = read_package_summary(root, name)
    deps = item.get("depends_on", []) if isinstance(item.get("depends_on"), list) else []
    dependency_summaries = [read_package_summary(root, dep) for dep in deps]
    team_name = team_name_for_initiative(initiative)
    assignment_kind = item.get("assignment_kind", "execution_ready")
    worker_name = integration_worker_name_for_package(name) if assignment_kind == "serial_integration_ready" else worker_name_for_package(name)
    assignment_id = f"{round_id}:{name}:{assignment_kind}"
    worktree_ref = package_worktree_ref(root, initiative, name, worktree_root_ref)
    resolved_worktree_path = str(resolve_worktree_ref(root, worktree_ref))
    assignment = {
        "assignment_id": assignment_id,
        "round_id": round_id,
        "initiative": initiative,
        "source_repo_root": str(root.resolve()),
        "package": name,
        "package_path": f".arbor/tasks/{name}",
        "team_name": team_name,
        "worker_name": worker_name,
        "runtime": "claude-code-agent-team",
        "isolation": "team-enter-worktree-required",
        "assignment_kind": assignment_kind,
        "allowed_until": item.get("allowed_until", "review"),
        "stop_before": item.get("stop_before"),
        "dependency_gate": item.get("dependency_gate", "satisfied"),
        "parallel_policy": item.get("parallel_policy"),
        "modification_scope": item.get("modification_scope"),
        "contract_inputs": item.get("contract_inputs", []),
        "contract_outputs": item.get("contract_outputs", []),
        "open_contract_requests": item.get("open_contract_requests", []),
        "branch": package_branch_name(initiative, name),
        "base_branch": None,
        "worktree_root_ref": normalize_worktree_root_ref(root, worktree_root_ref),
        "worktree_ref": worktree_ref,
        "resolved_worktree_path": resolved_worktree_path,
        "worktree_path": resolved_worktree_path,
        "worktree_hint": worktree_ref,
        "next_action": item.get("next_action"),
        "context_files": [
            parent_map_ref(initiative),
            f".arbor/maps/{initiative}/map.json",
            worker_dispatch_path(name),
            f".arbor/tasks/{name}/prd.md",
            f".arbor/tasks/{name}/task.md",
            f".arbor/tasks/{name}/task.json",
            f".arbor/tasks/{name}/context/impl.jsonl",
            f".arbor/tasks/{name}/context/review.jsonl",
            f".arbor/tasks/{name}/context/sources.jsonl",
        ],
        "dependency_summaries": [
            {
                "name": dep.get("name"),
                "state": dep.get("state"),
                "prd_status": dep.get("prd_status"),
                "execution_status": dep.get("execution_status"),
                "latest_checkpoint": dep.get("latest_checkpoint"),
                "latest_lead_checkpoint": dep.get("latest_lead_checkpoint"),
                "path": dep.get("path"),
            }
            for dep in dependency_summaries
        ],
    }
    write_worker_dispatch_packet(root, initiative, name, summary, dependency_summaries, assignment)
    stop_clause = f" 进入 {assignment['stop_before']} 前停止并报告。" if assignment.get("stop_before") else ""
    serial_clause = (
        "这是 serial_integration_ready 工作：你是隔离的 serial integration worker；main-session lead 只协调、审查和 checkpoint，must not implement this package directly。 "
        if assignment_kind == "serial_integration_ready"
        else ""
    )
    assignment["worker_prompt"] = (
        "使用语言：中文。 "
        f"Assignment ID: {assignment_id}. 每次 start/completion/blocker 消息都必须包含这个 ID。 "
        f"你是 Agent Team worker teammate '{worker_name}'，负责 sdd-kit package '{name}'，team runtime 为 '{team_name}'。 "
        "main Claude session 是 lead/orchestrator；不要再创建 nested orchestrator agent。 "
        f"{serial_clause}"
        f"worker session 必须从 source repo root='{assignment['source_repo_root']}' 或同一 git repo 的已注册 worktree 启动；如果当前 cwd 不在 git repo，立即报告 BLOCKER wrong_workspace。 "
        f"第一动作必须调用 EnterWorktree(path='{assignment['resolved_worktree_path']}')，然后验证 pwd/git root/branch='{assignment['branch']}'；在发送 WORKTREE_READY 前禁止 Read/Edit/Write/Bash/NotebookEdit 或任何实现动作。 "
        f"worktree_ref='{assignment['worktree_ref']}' 是 portable ref；resolved path 只用于当前机器 runtime。 "
        f"WORKTREE_READY 后先读 {worker_dispatch_path(name)}，再读其中列出的 map 与 package-local PRD/task/task.json/context files。 "
        f"完成时报告 changed artifacts；lead 会用 import-package-artifacts {name} --from-worktree {assignment['worktree_ref']} 回收 artifacts，lifecycle/control state 继续用 arbor helper 更新。 "
        f"本 assignment 类型是 {assignment['assignment_kind']}：从 task.json next_action={summary.get('next_action', {}).get('skill')} 推进到 {assignment['allowed_until']} 为止。{stop_clause} "
        "用 TaskUpdate 维护 shared Team task，用 SendMessage 汇报结构化块：WORKTREE_READY, WORKER_DONE, CONTRACT_REQUEST, WAITING_INPUT, BLOCKER, READY_FOR_INTEGRATION, or SHUTDOWN_ACK。 "
        "只拥有声明的 modification_scope；跨 package 缺口用 contract requests，不改 sibling；绝不读取/合并/复制 sibling branches 或 worktrees。 "
        "Shared/global wiring 属于 lead_serial serial integration worker lane，除非 owned_paths 明确包含；main-session lead must not implement package/product changes directly。 "
        "可以向 teammate workers 询问 producer/consumer contract 问题，但不能修改 sibling package state 或直接 patch producer packages。 "
        "如果 package work 已 reviewed，要求 lead 审查并记录 lead-integration checkpoint 后，下游才能依赖。 "
        "不要启动 downstream packages，不要把产品代码写进 .arbor/tasks，不要创建 PR、push、deploy 或执行 destructive actions。"
    )
    return assignment


def map_plan_agents(root: Path, initiative: str, max_parallel: int, actor: str, timestamp: str, worktree_root_ref: str | None = None) -> dict[str, Any]:
    if max_parallel < 1:
        raise ArborError("--max-parallel must be at least 1.")
    if max_parallel > 5:
        raise ArborError("--max-parallel must be 5 or less; keep the lead-owned worker pool bounded.")
    normalized_worktree_root_ref = normalize_worktree_root_ref(root, worktree_root_ref)
    check = map_check(root, initiative, timestamp)
    round_id = f"round-{uuid5(NAMESPACE_URL, f'arbor:{initiative}:{timestamp}').hex[:12]}"
    assignments = []
    candidates = check["execution_ready"] + check["prep_ready"]
    for item in candidates[:max_parallel]:
        assignments.append(assignment_context(root, initiative, item, check, round_id, normalized_worktree_root_ref))
    integration_assignments = [assignment_context(root, initiative, item, check, round_id, normalized_worktree_root_ref) for item in check["integration_ready"][:1]]
    runtime_reconciliation = {
        "check_active_workers": "派发前对齐 active packages、Team members 和 task ownership",
        "verify_assignment_ids": "worker 消息必须匹配 package execution.session；stale 或 duplicate workers 需要 stand down",
        "handle_waiting_input": "收到 WAITING_INPUT 后先由 lead 路由到 user/producer/context，再继续派发",
        "checkpoint_reviewed_packages": "reviewed package 需要 lead-integration 或 contract-update checkpoint 后，下游才能进入 implementation",
        "dispatch_integration_ready": "integration_ready 一次只派一个 serial integration worker；lead session 只协调/审查/checkpoint，不实现",
        "cleanup_when_idle": "没有 execution_ready/prep_ready/integration_ready/active worker 后，shutdown teammates 并 TeamDelete runtime",
    }
    plan = {
        "at": timestamp,
        "round_id": round_id,
        "actor": actor,
        "initiative": initiative,
        "team_name": team_name_for_initiative(initiative),
        "runtime": "claude-code-agent-team",
        "lead": "main-session",
        "isolation": "team-enter-worktree-required",
        "worktree_root_ref": normalized_worktree_root_ref,
        "worktree_root_path": str(resolve_worktree_ref(root, normalized_worktree_root_ref)),
        "max_parallel": max_parallel,
        "strategy": "lead-owned-rolling-worker-pool",
        "assignments": assignments,
        "runtime_events": sorted(PARALLEL_RUNTIME_EVENTS),
        "runtime_reconciliation": runtime_reconciliation,
        "execution_ready_count": len(check["execution_ready"]),
        "prep_ready_count": len(check["prep_ready"]),
        "integration_ready_count": len(check["integration_ready"]),
        "integration_ready": check["integration_ready"],
        "integration_assignments": integration_assignments,
        "blocked_count": len(check["blocked"]),
        "active_count": len(check["active"]),
        "complete_count": len(check["complete"]),
    }
    append_jsonl(map_context_dir(root, initiative) / "agent-assignments.jsonl", {"kind": "assignment_plan", **plan})
    append_parallel_runtime_event(
        root,
        initiative,
        "lead_reconcile",
        actor,
        timestamp,
        reason="map-plan-agents 已生成 runtime reconciliation snapshot",
        detail={
            "execution_ready_count": len(check["execution_ready"]),
            "prep_ready_count": len(check["prep_ready"]),
            "integration_ready_count": len(check["integration_ready"]),
            "blocked_count": len(check["blocked"]),
            "active_count": len(check["active"]),
        },
    )
    return plan
