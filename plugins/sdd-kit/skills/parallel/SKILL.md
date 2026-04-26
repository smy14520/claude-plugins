---
name: parallel
description: "Trellis-like autonomous package orchestrator for sdd-kit large initiatives. Runs map readiness checks, plans ready package assignments, injects package-local context, and dispatches worker agents that advance ready `.arbor/tasks/<package>/` boundaries through brainstorm/task/impl/review until reviewed, blocked, or decision-needed. Invoke only on explicit user request such as `/sdd-kit:parallel`, '用 parallel skill', or '并行推进'."
---

# Parallel — Trellis-like Package Orchestrator

`parallel` 是 sdd-kit 的一等统筹入口。用户执行它，表示授权 orchestrator 自主推进当前 ready package；如果用户想逐阶段人工审计，应直接使用 `/sdd-kit:brainstorm`、`/sdd-kit:task`、`/sdd-kit:impl`、`/sdd-kit:review`。

用户入口应尽量短：

```text
/sdd-kit:parallel
/sdd-kit:parallel knowledge-paid-system
用 parallel skill
并行推进 knowledge-paid-system
```

如果当前项目只有一个 `.arbor/maps/<initiative>/map.json`，用户可以省略 initiative 名；否则要求用户选择一个 initiative。

## 定位

```text
map creates package graph → [parallel] dispatches package pipelines → package-local brainstorm/task/impl/review → map unlocks downstream waves
```

Parallel 不重新判断 package graph，不手写业务方案。它是 Trellis-like orchestrator：

1. 找到 initiative map
2. 读取 `.arbor/maps/<initiative>/map.json`
3. 运行 deterministic readiness check
4. 生成 ready package assignments
5. 为每个 ready package 注入上下文
6. 启动最多 N 个 package dispatch worker agents
7. 每个 worker 在自己的 package boundary 内循环执行 `task.json.next_action.skill`
8. worker 遇到完成、阻塞或需要用户决策时停止并回报
9. 当前 wave 完成后重新 `map-check`，若 dependency 解锁则继续下一 wave

## 默认参数

- 默认并行度：2
- 最大并行度：4
- 默认模式：autonomous package pipeline
- `--plan-only`：只输出 assignment，不启动 agents
- `--max-parallel N` 或 `-j N`：指定并行度

示例：

```text
/sdd-kit:parallel                       # 自动选择唯一 map，默认并行 2，自主推进 ready packages
/sdd-kit:parallel knowledge-paid-system # 指定 initiative，默认并行 2
/sdd-kit:parallel -j 3                  # 最多 3 个 ready package worker
/sdd-kit:parallel --plan-only           # 只看计划，不启动 worker
```

## 人工审计路径

不要给 `parallel` 加“自动模式”参数。语义约定是：

- 用户显式调用阶段 skill：人工审计 / 人工控制。
- 用户显式调用 `parallel`：授权自主统筹推进，遇到无法安全判断的问题再反馈。

```text
# 人工审计路径
/sdd-kit:brainstorm .arbor/tasks/course-content
# 用户审 prd.md
/sdd-kit:task course-content
# 用户审 task.md
/sdd-kit:impl course-content T-001
/sdd-kit:review course-content T-001

# 自主统筹路径
/sdd-kit:parallel knowledge-paid-system
```

## 执行流程

### 1. Resolve initiative

- 如果用户显式给出 initiative：使用它。
- 如果未给出：扫描 `.arbor/maps/*/map.json`。
  - 0 个：停止，提示先用 map/brainstorm 创建 initiative map。
  - 1 个：自动使用。
  - 多个：停止，让用户指定 initiative。

### 2. Check readiness

运行：

```text
python3 plugins/sdd-kit/tools/arbor.py map-check <initiative> --json
```

判断：

- `ready`：可分发 package dispatch worker。
- `blocked`：依赖未完成、validation/state 阻塞、或 package 需要用户决策。
- `active`：已有 worker/claim/PR，不重复分发。
- `complete`：已 reviewed/completed/merged，不重复分发。
- `missing`：map 记录了 package 但 stub 不存在，应回 map 修复。

### 3. Plan assignments

运行：

```text
python3 plugins/sdd-kit/tools/arbor.py map-plan-agents <initiative> --max-parallel <N> --json
```

该命令会写入：

```text
.arbor/maps/<initiative>/context/agent-assignments.jsonl
```

### 4. Dispatch package workers

对 `assignments[]` 中每个 ready package 启动一个 package dispatch worker agent。

Worker prompt 必须包含：

- assignment 的 `worker_prompt`
- assignment 的 `context_files`
- 当前 package 的 `next_action`
- 明确 package 是 execution boundary
- 明确禁止修改 sibling package 的 `task.json`
- 明确禁止自动创建 PR / push / deploy / 破坏性动作
- 明确遇到 ambiguity / blocker / boundary drift / unsafe action 时停止并回报

### 5. Package worker loop

Worker 不是只执行一个阶段。它必须在自己的 package 内循环：

```text
while package is assignable:
  read .arbor/tasks/<package>/task.json
  inspect next_action.skill
  run the corresponding skill behavior:
    brainstorm → finalize package PRD/context
    task       → decompose T-xxx and freeze task definition
    impl       → implement the next ready T-xxx and run SelfCheck
    review     → independent semantic review for the implemented T-xxx
  validate package with arbor.py validate <package>
  stop if package reviewed/completed, blocked, needs_context, brainstorm_drift, needs_rework, user decision required, or unsafe external action required
```

Worker 根据 `next_action.skill` 执行：

- `brainstorm`：补全该 child package 的 `prd.md`，不拆 sibling package，不修改 map graph。
- `task`：拆该 package 的 T-xxx，写实 `task.md`，通过 `arbor.py add-child` / `add-context` / `freeze-definition` 更新 `task.json`。
- `impl`：执行该 package 的 next ready T-xxx；只做本地实现与 SelfCheck，不 commit / push / PR。
- `review`：用独立上下文审计该 package 的 next review target；review 不改代码。
- `user` / `none`：停止并回报。

### 6. Wave loop

当当前 batch 的 package workers 完成后，统筹层重新运行 `map-check`：

- 如果新 package 因依赖 reviewed/completed/merged 而 ready，继续按并行度启动下一批。
- 如果所有 package complete：结束。
- 如果剩余 package 都 blocked / missing / active：报告原因并结束本轮。

## 必须回报用户的情况

Autonomous 不等于静默猜测。Worker 遇到以下情况必须停止并回报 orchestrator/user：

1. 需求歧义：权限、金额、订单、退款、状态流转、角色边界、验收口径无法从 PRD/context 判断。
2. Acceptance 不可验证：无法写成命令或二元谓词。
3. Package 边界漂移：需要修改 sibling package 的生命周期状态，或当前 T-xxx 明显应提升为独立 package。
4. Dependency contract 不足：依赖 package 已 reviewed 但没有提供当前 package 所需 contract。
5. 技术阻塞：测试环境、依赖服务、迁移风险、不可恢复失败。
6. 安全/外部副作用：push、PR、部署、删除数据、改共享 infra、支付/认证/权限核心风险。
7. Review 语义漂移：实现符合 task 但 task/PRD 本身错误，进入 `brainstorm_drift` 或 `needs_rework`，不得强行继续。

## 依赖等待规则

Parallel 只 dispatch `map-check` 的 `ready` packages。

一个 package 只有在所有 package-level dependencies 满足以下之一时才 ready：

- dependency package `state` 是 `reviewed` / `completed`
- dependency package `execution.status` 是 `reviewed` / `merged`
- dependency package PR 是 `merged`

否则 downstream package 保持 blocked。

## 输出格式

每轮输出：

```text
Initiative: <initiative>
Mode: autonomous package pipeline
Dispatched: <package-a>, <package-b>
Completed this round: <package-a>
Blocked / needs decision: <package-c> reason=<reason>
Active: <package-d>
Complete overall: <package-e>
Next: <continue automatically if new ready wave exists, otherwise report final blockers>
```

如果 `--plan-only`：输出同样摘要，但不启动 worker。

## 核心规则

1. **一等入口** —— 用户不需要记 `map-check` / `map-plan-agents`。
2. **Parallel = autonomous orchestration** —— 显式阶段 skill 才是人工审计路径。
3. **Package-level only** —— 并行单位是 `.arbor/tasks/<package>/`，不是 T-xxx。
4. **Ready-only dispatch** —— 不启动 blocked package。
5. **Bounded parallelism** —— 默认 2，最多 4。
6. **Context injection, not global context** —— worker 只收到 map + target package + dependency summaries。
7. **No sibling mutation** —— worker 不修改 sibling package 状态。
8. **Wave by wave** —— 当前 wave 完成后重新 `map-check`，解锁 downstream 后继续。
9. **Stop on uncertainty** —— 需求、边界、验收、技术或安全无法判断时停止并回报。
10. **No implicit PR/worktree/push/deploy** —— 除非用户明确要求或项目指令要求。
11. **Review independence** —— review 必须在独立上下文中执行，不能由同一实现上下文自我背书。

## 本 skill 不做的事

- 不创建 package graph（用 map / brainstorm）
- 不判断 package boundary
- 不拆 initiative parent task
- 不把 blocked package 强行并行
- 不自动创建 worktree / branch / PR
- 不自动 push / merge / deploy
- 不在不确定时静默猜测
