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
- Readiness check: `python3 plugins/sdd-kit/tools/arbor.py map-check <initiative-name>`
- Agent Team assignment plan: `python3 plugins/sdd-kit/tools/arbor.py map-plan-agents <initiative-name> --max-parallel 3`

`map-plan-agents` emits assignments for `execution_ready` packages and `prep_ready` packages allowed by map-time `parallel_policy`. The user-facing orchestration entry is `/sdd-kit:parallel` or `并行推进 <initiative>`; the main session stays lead, creates an Agent Team worker pool, and dispatches worktree-isolated package workers for those assignments. Parallel uses Team messages for coordination and local checkpoint commits for code synchronization.

## Current framing

<当前对这个大项目/上位主题的一句话理解；为什么需要多个 executable packages。>

## Implementation framing

<Brainstorm 已确认的项目级实现前提：技术栈、源码/测试布局、运行命令、共享约束。全局约定应由用户确认后沉淀到 CLAUDE.md 或 `.claude/rules`；当前 initiative 特有约束写在这里或 package PRD 中。>

## Package graph

Package 是 branch/worktree/PR 执行边界；T-xxx 明细留在 package 内，不在 map 中展开。

| Package | Control path | Materialized | Boundary reason | Depends on | Parallel policy | Max phase before deps | Dependency gate | Wave | Contract inputs | Contract outputs | PRD status | Execution status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| <package> | `.arbor/tasks/<package>/` | yes/no | <why this is one executable package> | [] | independent / contract_dependent / hard_dependent | review/task/none | none/impl/review | W1 | <inputs> | <outputs> | draft | unclaimed | <notes> |

Materialized values:
- `yes` — `.arbor/tasks/<package>/` exists with `source_type=map-split` and `package_sizing=split_applied`
- `no` — map row exists but package stub has not been created yet; run `create-split-packages`

Parallel policy values:
- `independent` — no sibling dependency; can run through review.
- `contract_dependent` — can prepare without dependencies, but must stop before `dependency_gate`.
- `hard_dependent` — must wait for dependencies before even preparing.

## Execution waves

| Wave | Packages | Entry criteria | Exit criteria | Parallelism notes |
|---|---|---|---|---|
| W1 | <package-a> | <what must be true before starting> | <what unlocks next wave> | <serial/parallel notes> |
| W2 | <package-b, package-c> | <dependencies satisfied> | <review/contract stable> | <can run in parallel if contracts hold> |

## Cross-package contracts

| Contract | Producer package | Consumer packages | Status | Notes |
|---|---|---|---|---|
| <contract-name> | <package-a> | <package-b, package-c> | draft | <notes> |

Status values:
- `unresolved`
- `draft`
- `stable`
- `blocked`

## Dependency graph

```text
<package-a>
  -> <package-b>
  -> <package-c>
```

## Open blockers

- <blocker>

## Materialization command

```text
python3 plugins/sdd-kit/tools/arbor.py create-split-packages <initiative-name> \
  --package "<package>::<title>::<dep1,dep2>::<boundary reason>" \
  --actor map \
  --decision "package graph materialized from .arbor/maps/<initiative-name>/map.md"
```

## Orchestration / agent assignment

Default recommendation:
- User says: `/sdd-kit:parallel <initiative-name>` or `并行推进 <initiative-name>` to authorize main-session-led Agent Team worker-pool execution.
- Omit initiative only when there is a single `.arbor/maps/*/map.json`.
- Use explicit `/sdd-kit:brainstorm` / `/sdd-kit:task` / `/sdd-kit:impl` / `/sdd-kit:review` when the user wants manual review gates.
- `--plan-only` generates worker assignments without starting workers.
- Default and max parallelism are both 3.
- Dispatch `execution_ready` first, then `prep_ready`; `prep_ready` must stop before its dependency gate.
- Do not assign packages listed as blocked by `map-check`.

Context injection packet contains:
- this `map.md`
- `map.json`
- target package `context/worker-dispatch.md`
- target package `prd.md`, `task.md`, `task.json`, `context/*.jsonl`
- summaries of dependency packages
- lead/team runtime/worker/branch/worktree assignment metadata

## Recommended next move

1. <next package-local brainstorm or blocker to resolve>
