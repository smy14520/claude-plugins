---
initiative: <initiative-name>
status: draft | active | stable | archived
updated: YYYY-MM-DD
source_research: <research-topic | null>
---

# <initiative-name> map

<!-- 输出语言: 中文 -->
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
- Context injection plan: `python3 plugins/sdd-kit/tools/arbor.py map-plan-agents <initiative-name> --max-parallel 2`

`map-plan-agents` only emits assignments for ready packages whose dependencies are reviewed/completed/merged. The user-facing orchestration entry is `/sdd-kit:parallel` or `并行推进 <initiative>`; it runs check + plan and may dispatch autonomous package pipeline workers for those assignments.

## Project framing

<当前对这个大项目/上位主题的一句话理解。>

## Package graph

Package 是 branch/worktree/PR 执行边界；T-xxx 明细留在 package 内，不在 map 中展开。

| Domain | Package | Materialized | Boundary reason | Depends on | Execution wave | Contract inputs | Contract outputs | PRD status | Task aggregate | Execution owner/status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|
| <domain-name> | `.arbor/tasks/<package>/` | yes/no | <why this is one executable package> | [] | W1 | <inputs> | <outputs> | draft | not-started | unclaimed | <notes> |

Materialized values:
- `yes` — `.arbor/tasks/<package>/` exists with `source_type=map-split` and `package_sizing=split_applied`
- `no` — map row exists but package stub has not been created yet; run `create-split-packages`

PRD status values:
- `draft`
- `ready-for-task`
- `revising`
- `blocked`

T-xxx aggregate values:
- `not-started`
- `in-task`
- `ready`
- `in-impl`
- `in-review`
- `reviewed`
- `blocked`

Execution values are package-level only:
- branch/worktree/PR belong to `.arbor/tasks/<package>/`
- if a T-xxx needs its own PR, split a new package and reference it here

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

## Shared capabilities

- <shared capability and owning package>

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
- User says: `/sdd-kit:parallel <initiative-name>` or `并行推进 <initiative-name>` to authorize autonomous package pipeline execution.
- Omit initiative only when there is a single `.arbor/maps/*/map.json`.
- Use explicit `/sdd-kit:brainstorm` / `/sdd-kit:task` / `/sdd-kit:impl` / `/sdd-kit:review` when the user wants manual review gates.
- `--plan-only` generates assignments without starting workers.
- Start with default max parallelism 2.
- Increase to 3 only when packages are independent and contracts are stable.
- Do not assign packages listed as blocked by `map-check`.

Context injection packet contains:
- this `map.md`
- `map.json`
- target package `prd.md`, `task.md`, `task.json`, `context/*.jsonl`
- summaries of dependency packages

## Recommended next move

1. <next package-local brainstorm or blocker to resolve>
