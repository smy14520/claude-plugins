---
name: parallel
description: "Trellis-like main-session-led Agent Team worker pool for sdd-kit large initiatives. Runs map-check/map-plan-agents, uses map-time parallel_policy to classify execution_ready vs prep_ready packages, injects package-local context, and dispatches up to 3 worktree-isolated worker teammates. Invoke only on explicit user request such as `/sdd-kit:parallel`, '用 parallel skill', or '并行推进'."
---

# Parallel — Main-session lead + Agent Team worker pool

`parallel` 是 sdd-kit 的 Trellis-like 自主推进入口。用户执行它，表示授权**主会话作为 lead/orchestrator**，创建一个 runtime Agent Team 作为共享任务队列和 worker namespace，然后滚动派发最多 3 个 package worker。

如果用户想逐阶段人工审计，直接使用 `/sdd-kit:brainstorm`、`/sdd-kit:task`、`/sdd-kit:impl`、`/sdd-kit:review`。

```text
map writes package graph + parallel_policy
→ [parallel] main session records original base and creates Team runtime
→ each runnable package becomes one Team task + one worker teammate + one worktree/branch
→ workers use TaskUpdate/SendMessage for runtime coordination
→ reviewed package integrates to the main/session branch, validates, and becomes a local checkpoint commit
→ lead records the checkpoint, reruns map-check, and dispatches next runnable package from the updated base
→ final human review can soft-reset checkpoint commits back into an uncommitted diff
```

## 用户入口

```text
/sdd-kit:parallel
/sdd-kit:parallel knowledge-paid-system
/sdd-kit:parallel -j 3
/sdd-kit:parallel --plan-only
用 parallel skill
并行推进 knowledge-paid-system
```

- 默认并行度：3。
- 最大并行度：3。
- `--plan-only`：只输出 worker assignment，不启动 worker。
- 未指定 initiative 时，若只有一个 `.arbor/maps/*/map.json` 则自动使用；多个则要求用户指定。

## Readiness model

`map` 在生成 package graph 时就写入每个 package 的 `parallel_policy`：

```json
{
  "independence": "independent | contract_dependent | hard_dependent",
  "can_prepare_without_dependencies": true,
  "can_implement_without_dependencies": false,
  "max_phase_before_dependencies": "brainstorm | task | impl | review",
  "dependency_gate_phase": "none | impl | review",
  "reason": "..."
}
```

`parallel` 不重新猜需求是否独立，只执行 `map-check` 的分类：

- `execution_ready`：可以推进到 review；通常是独立 package，或依赖已 reviewed/completed/merged。
- `prep_ready`：依赖未完成，但允许先做 package-local brainstorm/task/context；worker 必须在 `stop_before` 前停下。
- `blocked`：自身缺上下文、validation failed、hard dependency 未满足、或当前 next_action 超过 policy 限制。

## 执行流程

1. Resolve initiative。
2. 记录 original base commit，供最终人工审计 reset 使用。
3. 运行：
   ```text
   python3 plugins/sdd-kit/tools/arbor.py map-check <initiative> --json
   ```
4. 运行：
   ```text
   python3 plugins/sdd-kit/tools/arbor.py map-plan-agents <initiative> --max-parallel <N> --json
   ```
   assignment 包含：`assignment_kind`、`allowed_until`、`stop_before`、`team_name`、`worker_name`、`branch`、`worktree_hint`、`context_files`、`worker-dispatch.md`、`worker_prompt`。
5. 创建 runtime Team：`TeamCreate(team_name="arbor-<initiative>")`。这不是另一个统筹 agent；统筹始终是主会话。
6. 为每个 assignment 创建 Team runtime task：`TaskCreate`，再用 `TaskUpdate(owner=<worker_name>)` 设 owner。
7. 为每个 assignment 启动 worker teammate：
   - `team_name=<team_name>`
   - `name=<worker_name>`
   - `isolation=worktree`
   - prompt 注入 `worker_prompt` + `context_files`
8. worker 在自己的 worktree/branch 内执行，并通过 `claim-package` / `set-execution` 记录 package-level branch/worktree/owner。
9. worker 使用 `TaskUpdate` + `SendMessage` 回报 start / completion / blocker / contract question。
10. 对 reviewed package，lead 合回主会话分支、解决冲突、运行 validation/tests、创建本地 checkpoint commit，并记录：
    ```text
    python3 plugins/sdd-kit/tools/arbor.py record-checkpoint <package> \
      --kind lead-integration \
      --sha <sha> \
      --branch arbor/<initiative>/<package> \
      --base-sha <base> \
      --actor parallel \
      --note "integrated after validation"
    ```
11. lead 重新 `map-check` / `map-plan-agents`；有新 runnable package 就从更新后的 base 启动新 worker/worktree，避免下游沿用 stale worktree。
12. 若 consumer 发现 producer contract 不足：consumer message producer + lead 并暂停；producer 负责 amendment/patch/checkpoint；lead 报告更新 checkpoint/base 后 consumer 再恢复。
13. 最终人工审计时保留 `.arbor` 状态；如用户要求，把 checkpoint commits 软复位回 uncommitted diff：`git reset --soft <original-base>` 后再 `git reset`。
14. 若无新 runnable package，报告 complete / blocked / active / missing。

## 状态源分层

```text
Team message / TaskList = runtime coordination
.arbor                  = durable package/map state
git checkpoint commits  = code synchronization
```

Team TaskList 不能替代 `.arbor`；Team message 不能替代 git checkpoint。

## Worker contract

每个 worker 只处理自己的 package boundary：

```text
.arbor/tasks/<package>/
```

Worker 必须：

- 先读 `.arbor/tasks/<package>/context/worker-dispatch.md`。
- 在自己的 worktree/branch 内执行；不要在 lead/orchestrator worktree 混写 diff。
- 使用 `TaskUpdate` 更新 Team task，用 `SendMessage` 向 lead/teammate 沟通。
- 不修改 sibling package 的 `task.json`。
- 不 patch producer package；发现 producer contract 缺口时 message producer + lead 后暂停。
- 不启动 downstream packages。
- reviewed 后请求 lead integration/checkpoint，不自行合并到主会话分支。
- 遵守 `assignment_kind` / `allowed_until` / `stop_before`。
- 不自动创建 PR / push / deploy。
- 不做破坏性动作。
- 遇到 ambiguity / blocker / boundary drift / unsafe action 时停止并回报。

Worker 在 package 内循环，但不能超过 assignment limit：

```text
read worker-dispatch.md + task.json
inspect next_action.skill
run corresponding skill behavior:
  brainstorm → finalize package PRD/context
  task       → decompose T-xxx and freeze task definition
  impl       → implement next ready T-xxx and run SelfCheck
  review     → independent semantic review
  amendment  → if clear package-local drift: append AMD-xxx + linked T-xxx
run arbor.py validate <package>
stop on reviewed/completed, blocked, needs_context, needs_rework,
        brainstorm_drift, stop_before, user decision, or unsafe external action
```

`prep_ready` worker 的典型行为是：依赖还没完成时可以先把 PRD/task/context 准备好，但在 `impl` 前停止，等待 dependency gate。依赖合回主会话分支并记录 checkpoint 后，下游实现应从更新后的 base 重新派发 worker/worktree，不沿用 stale worktree。

## Contract gap protocol

1. Consumer message producer worker and lead.
2. Consumer pauses before implementing against missing behavior.
3. Producer owns its amendment/patch and checkpoint.
4. Lead reports updated checkpoint/base; consumer resumes from that base.

## Worktree / branch isolation

Package 是执行隔离边界：

```text
package = Agent Team worker teammate + branch + worktree + diff boundary
```

Recommended naming from `map-plan-agents`：

```text
team runtime: arbor-<initiative>
worker:       pipeline-<package>
branch:       arbor/<initiative>/<package>
worktree:     .claude/worktrees/arbor-<initiative>/<package>
```

## Stop / escalate conditions

Autonomous 不等于静默猜测。Worker 必须停止并回报：

1. 需求歧义：权限、金额、订单、退款、状态流转、角色边界、验收口径无法判断。
2. Acceptance 不可验证：无法写成命令或二元谓词。
3. Package 边界漂移：需要修改 sibling state，或某 T-xxx 应提升为独立 package。
4. Dependency contract 不足：依赖 package 已完成但未提供当前 package 需要的 contract。
5. 技术阻塞：测试环境、依赖服务、迁移风险、不可恢复失败。
6. 安全/外部副作用：push、PR、部署、删除数据、共享 infra、支付/认证/权限核心风险。
7. Review 语义漂移：清晰 package-local 修正走 AMD-xxx + 新 T-xxx；语义不明确或边界漂移则停止回报。

## 输出格式

```text
Initiative: <initiative>
Mode: main-session lead + rolling Agent Team worker pool
Team runtime: arbor-<initiative>
Dispatched execution_ready: <package-a>, <package-b>
Dispatched prep_ready: <package-c> stop_before=impl
Completed this round: <package-a>
Blocked / needs decision: <package-d> reason=<reason>
Active: <package-e>
Complete overall: <package-f>
Next: <continue if new runnable package exists, otherwise final blockers>
```

## 核心规则

1. **主会话是统筹层**；不要再创建一个 orchestrator teammate。
2. **Agent Team 是 runtime worker pool**；只在确实有并发 package 时使用。
3. **最多 3 个并发 worker**；某个 worker reviewed 后，lead 集成、验证、checkpoint，再从更新后的 base 派发下一个 runnable package。
4. **Package-level only**；并行单位是 `.arbor/tasks/<package>/`，不是 T-xxx。
5. **Map-time policy**；是否能提前 prepare/implement 由 `parallel_policy` 决定。
6. **Context injection, not global context**；`worker-dispatch.md` 是 worker 的 `.current-task` 等价物。
7. **No sibling mutation**。
8. **Stop on uncertainty**。
9. **Forward-only amendment**；不重写旧 PRD/task，只追加 AMD-xxx 与新 T-xxx。
10. **No implicit PR/worktree cleanup/push/deploy**，除非用户或项目指令明确要求。
11. **Review independence**；review 必须独立上下文，不能自我背书。

## 本 skill 不做

- 不创建 package graph（map / brainstorm）。
- 不重判 package boundary。
- 不把 blocked package 强行并行。
- 不绕过用户授权自动 push / merge / deploy。
- 不在不确定时静默猜测。
