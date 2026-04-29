---
initiative: <initiative-name>
status: draft | active | stable | archived
updated: YYYY-MM-DD
source_research: <research-topic | null>
---

# <initiative-name> map
<!--
  Map 是 large initiative 的 package graph / execution waves 导航，不是 PRD，也不是 task。
  不要创建 `.arbor/tasks/<initiative-name>/`。
  只有下方列出的 executable packages 才应该成为 `.arbor/tasks/<package>/`。
  package graph 确认后应 materialize child package stubs；T-xxx 明细留在每个 package 内，不在 map 中展开。
  map.md 是人类导航；map.json 是机器可读统筹状态源。
-->

## Machine-readable coordination

- Human map: `.arbor/maps/<initiative-name>/map.md`
- Machine state: `.arbor/maps/<initiative-name>/map.json`
- Agent assignment log: `.arbor/maps/<initiative-name>/context/agent-assignments.jsonl`
- Readiness check: arbor helper `map-check`
- Dynamic assignment plan: arbor helper `parallel-schedule`

`parallel-schedule` 会按当前 map/package state 选择 serial critical-path、parallel execution、parallel prep 或 serial integration lane。`integration_ready` 是 lead-owned serial work，但实现仍由一个隔离的 serial integration worker 执行；main session 保持 lead 角色，只协调、审查和 checkpoint，不直接实现 package/product diff。面向用户的统筹入口是 `/sdd-kit:parallel` 或 `并行推进 <initiative>`。Parallel 用 Team messages 协调 runtime work，用 contract requests 表达跨 package 缺口，用 lead/mainline checkpoints 同步代码事实。

## Current framing

<当前对这个大项目/上位主题的一句话理解；为什么需要多个 executable packages。>

## Implementation framing

<Brainstorm 已确认的项目级实现前提：技术栈、项目形态、前后端关系、repo baseline/scaffold、数据/权限/测试策略、源码/测试布局、运行命令、共享约束。全局约定应由用户确认后沉淀到 CLAUDE.md 或 `.claude/rules`；当前 initiative 特有约束写在这里或 package PRD 中。若这些前提缺失，map 不应 materialize child package stubs，应回 brainstorm/user 澄清。>

## Package graph

Package 是 branch/worktree/PR 执行边界；T-xxx 明细留在 package 内，不在 map 中展开。

| Package | Control path | Materialized | Boundary reason | Write scope | Shared integration scope | Integration role | Depends on | Parallel policy | Max phase before deps | Dependency gate | Wave | Contract inputs | Contract outputs | PRD status | Execution status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| <package> | `.arbor/tasks/<package>/` | yes/no | <中文说明为什么这是一个 executable package> | <owned paths / package-local scope；用中文解释范围> | <shared/global paths if any；用中文解释集成敏感点> | package / lead_serial | [] | independent / contract_dependent / hard_dependent | review/task/none | none/impl/review | W1 | <inputs> | <outputs> | draft | unclaimed | <中文备注> |

Materialized values:
- `yes` — `.arbor/tasks/<package>/` 已存在，且 `source_type=map-split`、`package_sizing=split_applied`
- `no` — map row 已存在但 package stub 还没创建；运行 `create-split-packages`

Parallel policy values:
- `independent` — 没有 sibling 依赖，可推进到 review。
- `contract_dependent` — 依赖未完成时可先准备，但必须停在 `dependency_gate` 前。
- `hard_dependent` — 依赖未完成前连准备也不应开始。

Integration role values:
- `package` — 普通 package worker scope。
- `lead_serial` — shared/global integration lane；会进入 `integration_ready`，并一次只派一个 serial integration worker，不进入普通 worker pool，也不由 main session 直接实现。

Write scope notes:
- Package workers 只拥有声明的 scope。
- Shared center files、global wiring、DI、routes、migrations、E2E、repo-wide config 默认属于 serial integration worker work；除非某个 package 显式拥有这些路径。lead session 只审查/checkpoint，不直接实现。
- `summary` / `reason` / `boundary_reason` / 表格说明等人读内容默认用中文；字段名、enum、路径、命令保持英文。

## Execution waves

| Wave | Packages | Entry criteria | Exit criteria | Parallelism notes |
|---|---|---|---|---|
| W1 | <package-a> | <开始前必须满足什么> | <什么事实解锁下一 wave> | <串行/并行说明> |
| W2 | <package-b, package-c> | <依赖已满足> | <review/contract 已稳定> | <契约成立时可并行> |

## Cross-package contracts

| Contract | Producer package | Consumer packages | Status | Notes |
|---|---|---|---|---|
| <contract-name> | <package-a> | <package-b, package-c> | draft | <中文说明契约内容与稳定条件> |

Status values:
- `unresolved`
- `draft`
- `stable`
- `blocked`

## Contract requests

Durable requests 写在 `map.json.contract_requests[]`，由 arbor helper `upsert-contract` 幂等管理。

| ID | Consumer | Producer | Status | Request | Resolution |
|---|---|---|---|---|---|
| CR-001 | <package-b> | <package-a> | open | <需要 producer 提供的稳定 output/capability> | <可选 resolution> |

Status values: `open`, `accepted`, `fulfilled`, `rejected`, `superseded`.

## Dependency graph

```text
<package-a>
  -> <package-b>
  -> <package-c>
```

## Open blockers

- <blocker>

## Materialization

Package graph 确认后使用 arbor helper `create-split-packages`。具体参数以 `sdd-arbor create-split-packages --help` 为准。传入的 `boundary_reason` / `parallel_reason` 默认写中文。

## Orchestration / agent assignment

Default recommendation:
- 用户说 `/sdd-kit:parallel <initiative-name>` 或 `并行推进 <initiative-name>`，表示授权 main-session-led Agent Team worker-pool execution。
- 只有存在唯一 `.arbor/maps/*/map.json` 时才省略 initiative。
- 用户需要人工 review gates 时，显式使用 `/sdd-kit:brainstorm` / `/sdd-kit:task` / `/sdd-kit:impl` / `/sdd-kit:review`。
- `--plan-only` 只生成 worker assignments，不启动 workers。
- 默认和最大并行度都是 3。
- 先派发 `execution_ready`，再派发 `prep_ready`；`prep_ready` 必须停在 dependency gate 前。
- `integration_ready` 一次只派一个 serial integration worker assignment；不要放进普通 worker pool，也不要由 main session 实现。
- 不派发 `map-check` 标记为 blocked 的 packages。
- Downstream implementation 只能依赖 completed/merged packages 或 lead checkpoints，不能只依赖 `reviewed`。

Context injection packet contains:
- this `map.md`
- `map.json`
- target package `context/worker-dispatch.md`
- target package `prd.md`, `task.md`, `task.json`, `context/*.jsonl`
- dependency packages 摘要
- lead/team runtime/worker/branch/worktree assignment metadata

## Recommended next move

1. <下一步 package-local brainstorm 或要先解决的 blocker>
