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

<!-- Active PRD-first package artifact. Brainstorm owns this file until finalized; impl/review execute and audit this PRD directly. -->

## What I already know

- <已由用户确认、repo / research 支持，或当前明确可采用的事实 / 决策>

## Requirements (evolving)

- <每轮回答后更新：已经确认或当前采用的需求>

## Acceptance Criteria (evolving)

- [ ] <每轮回答后更新：用户可确认、impl/review 可验证的验收项>

## Open Questions

- <当前下一个最高价值问题；已回答后移走或改写>

## Interview Log

<!-- 只记录关键问题、用户选择/回答、由此产生的需求变化；不要保存完整聊天流水。 -->

| Turn | Question | User answer / choice | Requirement change |
|---|---|---|---|
| 001 | <问了什么> | <用户怎么选 / 怎么回答> | <新增、修改或排除什么需求> |

## 背景与问题

<为什么现在要做这件事？当前痛点 / 触发条件 / 业务上下文是什么？>

## 目标 / Desired outcomes

- <本 package 交付的结果 1>
- <结果 2>

## 本次范围

### In scope

- <本 package 明确要做的内容 1>

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

## Technical Framing

<!-- PRD 必须收敛承重技术边界，避免 impl 自由发挥。未知项放 Open Questions；不需要项明确 N/A。 -->

- Existing stack / framework:
- Auth / permissions:
- Frontend / backend boundary:
- Data model / persistence:
- Admin / ops surface:
- External integrations:
- Testing strategy:
- Migration / rollout / rollback:

## 方案草图 / Proposed approach

<高层方案。强调如何满足场景、technical framing 与交付物，不写实现步骤流水账。>

## Boundary decision

- Package kind: single
- Boundary status: fits_package
- Why this boundary works: <为什么当前范围可以作为需求 / 执行 / 评审 / 回滚边界>
- Execution unit: package PRD scope; progress lives in `task.json` `slices` via `sdd-arbor mark-slice`.

## Slices

<!-- Brainstorm 定稿前写好。PRD 只定义 slice 需求和顺序；impl 进度通过 sdd-arbor mark-slice 写入 task.json。每个 slice 必填 完成标志；其余字段按 slice 实际涉及范围取舍——涉及就写，不涉及整条省略。不分存量/新项目。完成标志 vs Acceptance Criteria：AC 是用户视角的整体验收，完成标志是每 slice 的技术 done-condition，每条 AC 应能追溯到 1 个或多个 slice 的完成标志组合。 -->

### S-001: <有数据、有代码、有测试的 slice>

- 完成标志：<一句话可验证的 done-condition>
- 数据/schema：<涉及表/migration 时写；标注 [new]/[existing]；可指向 artifacts/data-model.sql>
- 代码锚点：<涉及模块/文件/接口/页面时写；标注 [new]/[existing]>
- 测试：<Testing strategy 要求时写>

### S-002: <纯代码变更的 slice，例如 UI 或业务逻辑>

- 完成标志：<...>
- 代码锚点：<...>
- 测试：<...>

### S-003: <最终验收 / 自检切片>

- 完成标志：<关键路径、边界 case、未授权/异常路径都已验证>
- 测试：<...>

## 关键约束（仅保留承重约束）

- <真正会影响实现边界的约束>

## 数据 / 接口备注（按需）

### 数据 / 状态

- <涉及的状态、表、缓存、队列、幂等键等>

### 接口 / 集成

- 上游:
- 下游:
- 配置 / 环境:

## 验证重点

- <必须验证的行为 1>
- <必须覆盖的失败路径 2>

## 风险 / 开放问题 / 假设

### Open questions

- <会影响实现或 review 的未决项；PRD 定稿前 blocking 项必须解决>

### Assumptions

| Assumption | Level | Source | If false | Resolution / handling |
|---|---|---|---|---|
| <当前暂时成立的前提> | blocking / important / optional | <SRC-... / 用户确认 / 代码事实> | <会影响什么> | <定稿前解决 / 记录为风险 / 后续确认> |

### Risks

- <继续推进时必须显式暴露的风险>

## Amendments / Forward-only corrections

<!--
Append-only after impl/review has started.
Use AMD-001, AMD-002, ...
Do not rewrite old requirements silently; record wrong/correct/affects/source.
-->

| ID | Date | Wrong / obsolete requirement | Correct rule | Affects | Source |
|----|------|------------------------------|--------------|---------|--------|

## Sources

| ID | Type | Location | Title | Why it matters |
|----|------|----------|-------|----------------|
| SRC-LOCAL-001 | local-file | `src/...:12-48` | <title> | <why> |
"""


def review_template(name: str, timestamp: str) -> str:
    date = timestamp[:10]
    return f"""---
package: {name}
updated: {date}
---

# Review log: {name}

Append-only semantic audit entries for package-level PRD scope.
Current lifecycle state lives in `task.json`.
"""
