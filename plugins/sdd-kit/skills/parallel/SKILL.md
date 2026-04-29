---
name: parallel
description: "Automatic dynamic throughput optimizer for sdd-kit large initiatives. The main session stays lead/orchestrator and never implements package/product diff; it uses arbor parallel-schedule to switch between serial critical-path worker, bounded Agent Team worker pool, dependency-safe prep, and one serial integration worker. Applies safe self-healing helpers before asking the user. Invoke only on explicit user request such as `/sdd-kit:parallel`, '用 parallel skill', or '并行推进'."
---

# Parallel — dynamic lead + visible workers

`parallel` 是 sdd-kit 的自动吞吐优化入口。用户调用它表示希望提效；这不是一次性的“串行/并行”选择，而是运行中持续切换 lane 的能力。

主会话始终是 lead/orchestrator：协调、审查、checkpoint、回收 artifact、清理 runtime；不直接实现 package/product diff。即使当前只有一个 critical-path package 可做，也派发一个 single worker，保留 lead/worker 边界。Agent Team 是默认 runtime，因为它提供 iTerm 可见窗口和可直接交互的 worker；worktree isolation 由显式 `EnterWorktree` gate 保证。

```text
parallel-schedule
→ apply safe self-healing helpers
→ report lane switches, without waiting for confirmation
→ dispatch serial critical-path worker if only one package is runnable
→ dispatch Team worker pool when multiple independent packages open
→ dispatch one serial integration worker for lead_serial shared/global work
→ finish-worker / reconcile-package on worker reports
→ repeat until complete or true blocker
```

## 用户入口

```text
/sdd-kit:parallel
/sdd-kit:parallel <initiative>
/sdd-kit:parallel -j 3
/sdd-kit:parallel --plan-only
用 parallel skill
并行推进 <initiative>
```

- 默认并行度：5；最大并行度：5。
- `--plan-only`：只输出 schedule/assignment，不启动 worker。
- 未指定 initiative 时，若只有一个 `.arbor/maps/*/map.json` 则自动使用；多个则要求用户指定。

## Lane model

`parallel` 每轮先运行：

```text
sdd-arbor parallel-schedule <initiative> --max-parallel 5 --json
```

`sdd-arbor` 是 plugin `bin/` 中的 wrapper。不要假设业务项目根目录存在 `tools/arbor.py`。

可能 lane：

- `serial_critical_path`：只有一个 execution-ready package，派一个 worker；lead 不实现。
- `parallel_execution`：多个独立 `execution_ready`，启动/扩充 Agent Team worker pool，最多 5。
- `parallel_prep`：execution lane 有空位且存在 dependency-safe prep work，自动填充 brainstorm/task prep worker。
- `serial_integration`：`lead_serial` shared/global integration，一次只派一个 integration worker。
- `blocked`：没有可派发 work；先看 self-healing，只有 true blocker 才停。
- `complete`：所有已知 package 已有稳定完成事实。

Lane switch 只汇报，不等待确认。只有这些 true blockers 才停下来问用户：product decision、permission/destructive-risk、missing external context、unrecoverable state。

## Four boundaries

1. **Write permission boundary**：worker 只改 `modification_scope.owned_paths` 或 package PRD/task 明确归属的实现范围；shared/global paths 不归普通 worker。
2. **Contract boundary**：跨 package 缺口通过 `contract_requests`，consumer 不 patch producer internals。
3. **Mainline boundary**：worker 不读、不 merge、不 copy sibling branch/worktree；downstream implementation 只依赖 completed/merged/`lead-integration`/`contract-update` checkpoint。
4. **Integration boundary**：global wiring、DI、routes、migration ordering、repo-wide config、E2E assembly 进入 `lead_serial` serial integration worker lane；主会话 lead 只审查/checkpoint。

## Self-healing helpers

Recoverable friction 先走 helper，不升级给用户：

```text
parallel-schedule        # 选择 lane / assignments / true blockers
export-worker-context    # 修复 missing worker-dispatch/context packet
reconcile-package        # 清理 stale blocker / stale assignment / recoverable package state
finish-worker            # import artifacts + validate + runtime event + next schedule
add-context-batch        # 原子追加 context JSONL，避免 worker 手写文件
upsert-contract          # 幂等创建/更新 contract request
```

`WAITING_INPUT` 先路由到这些 helper；只有 helper 返回不可恢复、需要产品判断、权限或外部上下文时才问用户。

## Lead loop

每次 worker start / completion / blocker / idle 都执行同一套 loop：

```text
record runtime event when useful
→ run parallel-schedule
→ apply recommended self-healing when safe
→ verify assignment_id against package execution.session
→ route WAITING_INPUT / BLOCKER / CONTRACT_REQUEST
→ finish-worker when a worker reports changed artifacts
→ if reviewed: inspect output and record lead-integration / contract-update checkpoint if accepted
→ rerun parallel-schedule
→ dispatch next lane assignment(s)
→ if complete/no active runtime: shutdown workers + TeamDelete
```

关键规则：

- `map-check` / `parallel-schedule` 是调度事实源；Team idle 不是 durable truth。
- `reviewed` without lead checkpoint 不解锁 downstream implementation。
- `finish-worker` 默认回收 `prd.md`、`task.md`、`review.md`、`context/*.jsonl`，不覆盖 worker `task.json`。
- 直接追加 machine-readable context 时用 `add-context` / `add-context-batch`，不要手写 `context/*.jsonl`。
- contract gap 用 `upsert-contract`，避免重复 CR 或错误 ID。

## Bootstrap

1. Resolve initiative。
2. 记录 original base commit，供最终人工审计 reset 使用。
3. 运行 `sdd-arbor parallel-schedule <initiative> --max-parallel 5 --json`。
4. 如需创建 Team：`TeamCreate(team_name="arbor-<initiative>")`。不要创建 nested orchestrator teammate。
5. 对 schedule 里的 assignments：先 `claim-package` 写 owner/branch/worktree/session；再确保 package worktree/branch；然后 spawn worker。
6. `worktree_root` 默认 project sibling：`../arbor-worktrees/<project-name>`。`.arbor` 中只持久记录 portable ref，不写本机 absolute path。

## Dispatch

对每个 selected assignment：

1. **Pre-claim before spawn**：`claim-package <package> --owner <worker_name> --branch arbor/<initiative>/<package> --worktree <worktree_ref> --session <assignment_id>`。
2. 确保 package worktree 位于 `resolved_worktree_path`，branch 为 assignment branch。
3. 创建/更新 Team task owner。
4. 启动 worker teammate，prompt 注入 `worker_prompt`。
5. Worker 第一动作必须 `EnterWorktree(path=<resolved_worktree_path>)` 并汇报 `WORKTREE_READY`；此前禁止读写或实现动作。

`serial_integration` 使用同一流程，但一次最多派一个 integration worker。

## Worker contract

Worker 必须：

- 第一动作进入并验证 package worktree；`WORKTREE_READY` 前不读写。
- 先读 `.arbor/tasks/<package>/context/worker-dispatch.md`。
- 每条 report 带当前 `assignment_id`。
- 用结构化 block：`WORKTREE_READY`、`WORKER_DONE`、`CONTRACT_REQUEST`、`WAITING_INPUT`、`BLOCKER`、`READY_FOR_INTEGRATION`、`SHUTDOWN_ACK`。
- 只改 declared modification scope；不改 sibling package state；不 patch producer internals。
- 不读/merge/copy sibling branch/worktree。
- 遵守 `assignment_kind` / `allowed_until` / `stop_before`。
- reviewed 后请求 lead integration/checkpoint，不自行合并到主会话分支。
- 不自动 PR/push/deploy，不做破坏性动作。

Package-local 清晰 drift 可走 forward-only amendment；语义不清或跨边界 drift 则停止。

## Contract gap protocol

1. Consumer sends `CONTRACT_REQUEST` to producer worker and lead, then pauses.
2. Lead runs `upsert-contract` to write durable `contract_requests[]`.
3. Producer owns its amendment/patch if the gap is in producer scope.
4. Lead reviews producer result and records `contract-update` or `lead-integration` checkpoint.
5. Consumer resumes only from updated mainline base.

## Runtime cleanup protocol

Team 是 runtime，不是 durable state：

- stale/duplicate/completed worker：send stand down / shutdown request。
- 本轮无 dispatchable work 且无 active worker：shutdown all teammates, then `TeamDelete`。
- 保留 `.arbor` state、git checkpoints、branches/worktrees；不隐式删除 worktree/branch，除非用户明确授权。

## 输出格式

```text
Initiative: <initiative>
Mode: automatic dynamic parallel
Lane: <serial_critical_path | parallel_execution | parallel_prep | serial_integration | blocked | complete>
Team runtime: arbor-<initiative>
Round: <round_id>
Dispatched: <package assignment_id=... lane=...>
Self-healing: <applied/recommended/none>
Checkpointed: <package | none>
Blocked / needs decision: <package reason=... | none>
Active: <package | none>
Cleanup: <shutdown complete | kept because active/blocked | blocked reason>
Next: <continue / waiting for decision / complete>
```

## 本 skill 不做

- 不创建 package graph（map 负责）。
- 不重判 package boundary（map-time policy/scope 负责）。
- 不把 blocked package 强行并行。
- 不绕过用户授权 push / merge / deploy / destructive cleanup。
- 不把 Team runtime 当 durable state。
