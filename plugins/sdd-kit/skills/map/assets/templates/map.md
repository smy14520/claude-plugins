---
initiative: <initiative-name>
status: draft | active | stable | archived
updated: YYYY-MM-DD
source_research: <research-topic | null>
---

# <initiative-name> map
<!--
  Map 先做 boundary routing；只有 split 后才维护 package graph / execution waves。
  不要创建 `.arbor/tasks/<initiative-name>/`。
  如果判断为 single package，应创建/确认 `.arbor/tasks/<package>/` 并记录 fits_package，而不是强行维护 map。
  如果判断为 split packages，只有下方列出的 executable packages 才应该成为 `.arbor/tasks/<package>/`。
  package graph 确认后应 materialize child package stubs；T-xxx 明细留在每个 package 内，不在 map 中展开。
  map.md 是人类导航；map.json 是机器可读统筹状态源。
-->

## Machine-readable coordination

- Human map: `.arbor/maps/<initiative-name>/map.md`
- Machine state: `.arbor/maps/<initiative-name>/map.json`
- Readiness check: arbor helper `map-check`

`map-check` 只报告 ready / blocked / active / complete / missing，不自动派发执行。需要推进时，按输出显式进入对应 package 的 `brainstorm` / `task` / `impl` / `review`。

## Boundary routing decision

本文件只在 route decision 为 `split packages` 后实例化；`single package` / `back to brainstorm` 只应出现在临时 route 输出或 rejected options 中。

- Decision: split packages
- Why: <为什么当前 framing 应拆成多个 executable packages>
- Rejected options: <为什么没有选择 single package 或 back to brainstorm>

## Current framing

<当前对这个需求/上位主题的一句话理解；如果 split，说明为什么需要多个 executable packages。>

## Implementation framing

<Brainstorm 已确认的项目级实现前提：技术栈、项目形态、前后端关系、repo baseline/scaffold、数据/权限/测试策略、源码/测试布局、运行命令、共享约束。全局约定应由用户确认后沉淀到 CLAUDE.md 或 `.claude/rules`；当前 initiative 特有约束写在这里或 package PRD 中。若这些前提缺失，map 不应 materialize child package stubs，应回 brainstorm/user 澄清。>

## Package graph

Package 是需求/评审/回滚边界；T-xxx 明细留在 package 内，不在 map 中展开。

| Package | Control path | Materialized | Boundary reason | Depends on | Wave | PRD status | Execution status | Notes |
|---|---|---|---|---|---|---|---|---|
| <package> | `.arbor/tasks/<package>/` | yes/no | <中文说明为什么这是一个 executable package> | [] | W1 | draft | unclaimed | <中文备注> |

Materialized values:
- `yes` — `.arbor/tasks/<package>/` 已存在，且 `source_type=map-split`、`package_sizing=split_applied`
- `no` — map row 已存在但 package stub 还没创建；运行 `create-split-packages`

## Execution waves

| Wave | Packages | Entry criteria | Exit criteria | Notes |
|---|---|---|---|---|
| W1 | <package-a> | <开始前必须满足什么> | <什么事实解锁下一 wave> | <中文说明> |
| W2 | <package-b, package-c> | <依赖已满足> | <完成或 merged> | <中文说明> |

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

Durable requests 写在 `map.json.contract_requests[]`，由 arbor helper `record-contract-request` 管理。

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

Package graph 确认后使用 arbor helper `create-split-packages`。具体参数以 `sdd-arbor create-split-packages --help` 为准。传入的 `boundary_reason` 默认写中文。

## Recommended next move

1. <下一步 package-local brainstorm / task / impl / review，或要先解决的 blocker>
