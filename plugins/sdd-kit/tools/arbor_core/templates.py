from __future__ import annotations


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

<!-- Executable package PRD/context artifact. Brainstorm skill owns this file after clarified package framing. -->

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
- Why this is one executable package: <为什么当前范围可以作为一个需求/评审/回滚边界>
- Rejected split candidates: <哪些 slice 被考虑过但不需要独立 package；原因是什么>
- T-xxx 语义: package-local control / acceptance / review 单元

## 拆解线索 / 实现切片建议

- Slice A:
- Slice B:
- 依赖顺序提示:
- 注意: 这些 slice 后续会变成 package-local T-xxx

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

## Amendments / Forward-only corrections

<!--
Append-only after task/impl/review has started.
Use AMD-001, AMD-002, ...
Do not rewrite old requirements or renumber existing T-xxx.
Task appends new T-xxx linked by source_amendment/corrects.
-->

| ID | Date | Wrong / obsolete requirement | Correct rule | Affects | Source |
|----|------|------------------------------|--------------|---------|--------|

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
- [ ] Package 可作为一个需求/评审/回滚边界；若其实是 large initiative，未 finalize 本文件，已输出 clarified framing 并交给 `map`
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

<!--
  任务定义约定（强制执行）：
  - 禁止 wikilinks。本文件应自包含。
  - 禁止高层决策。每个任务仅包含可执行操作。
  - ID 只允许追加，不得重新编号；T-xxx 只在本 package 内唯一。
  - Package 是需求/评审/回滚边界；T-xxx 是 package-local control / acceptance / review 单元。
  - 每条验收条件必须是可执行命令或二元谓词。
  - 每个任务必须有 task-local context、sources 和 ready-check。
  - impl 不得修改本文件；执行状态只写入 task.json。
  - review 不得修改本文件；审计记录追加到 review.md，latest review state 写入 task.json。
  - Definition frozen 表示已有 T-xxx 不可改写；task skill 仍可为 AMD-xxx 追加新 T-xxx。
  - Amendment task 必须写 source-amendment/corrects，并包含 increment + regression acceptance。
-->

## 概览

- 来源: `prd.md`
- 模式: {mode}
- Package boundary: `.arbor/tasks/{name}/`
- T-xxx scope: package-local control / acceptance / review
- Boundary sizing decision from brainstorm/map: <fits_package | split_applied> — <为什么当前 package 边界成立；若拆过，列出来源/去向 package>
- Parent map / initiative: <.arbor/maps/<initiative>/map.md | none>
- Package readiness: 所有 required T-xxx 通过 review，且无 package-level blocker
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
  source-amendment: AMD-001        # optional; only for forward-only correction tasks
  corrects: [T-003]               # optional; old T-xxx this task amends/replaces
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
    - increment: <binary predicate or command for this task>
    - regression: <predicate/command proving corrected old behavior is not broken>
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
A single T-xxx approval does not mean the package is ready; package readiness is aggregated from all required child tasks.
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

<!-- Large initiative package graph. Map skill owns this file; map.json is the machine-readable coordination source. -->

## 当前 framing

<这个 initiative 为什么需要多个 executable packages？>

## Implementation framing

<Brainstorm 阶段已经明确的项目级实现前提：技术栈、项目形态、前后端关系、repo baseline/scaffold、数据/权限/测试策略、源码/测试布局、运行命令、共享约束。全局约定应由用户确认后沉淀到 CLAUDE.md 或 `.claude/rules`；当前 initiative 特有约束写在这里或 package PRD 中。若这些前提缺失，map 不应 materialize child package stubs，应回 brainstorm/user 澄清。>

## Package graph

> 人读内容默认写中文；字段名、enum、路径、命令保持英文。

| Package | Materialized | Depends on | Wave | Boundary reason | PRD status | Execution status | Notes |
|---|---|---|---|---|---|---|---|
| `.arbor/tasks/<package>/` | no | [] | W1 | <中文说明为什么这是一个 executable package> | draft | unclaimed | <中文备注> |

## Cross-package contracts

- <package-a> → <package-b>: <contract / dependency>

## Contract requests

| ID | Consumer | Producer | Status | Request | Resolution |
|---|---|---|---|---|---|
| CR-001 | <package-b> | <package-a> | open | <needed stable output/capability> | <optional> |

## Execution waves

- W1: <packages with no package dependency blockers>
- W2: <packages unlocked after W1 packages are completed or merged>

## Current blockers

- <blocker>

## Orchestration note

Map 只负责 package graph、依赖和 blocker 导航，不自动创建 Team、不派 worker。需要推进时，按 `map-check` 输出逐个进入对应 package 的 brainstorm/task/impl/review。

## Next orchestration check

Run:

```text
sdd-arbor map-check {initiative}
```
"""
