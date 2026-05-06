---
name: MM-DD-<topic-slug>
status: draft            # draft | ready | revising | superseded
date: YYYY-MM-DD
package: .arbor/tasks/MM-DD-<topic-slug>/
tags: []                 # optional
supersedes:              # optional, remove if N/A
---

# MM-DD-<topic-slug>
<!-- Active brainstorm PRD draft. Seed this at brainstorm start, update it after every user answer, and finalize only through sdd-arbor finalize-brainstorm. -->
<!-- 正文中的关键判断、场景、风险可用 [SRC-XXX] 标注来源 -->

## What I already know

- <已由用户确认、repo / research 支持，或当前明确可采用的事实 / 决策>
- <不要把未确认假设写成事实；放到 Open Questions 或 Assumptions>

## Requirements (evolving)

- <每轮回答后更新：已经确认或当前采用的需求>
- <形成初步 package scope 后，把扩展扫视中纳入本次 PRD scope 的项写到这里或 In scope>

## Acceptance Criteria (evolving)

- [ ] <每轮回答后更新：用户可确认、impl/review 可验证的验收项>
- [ ] <覆盖核心路径；PRD 定稿前补上关键失败 / 边界路径>

## Open Questions

- <当前下一个最高价值问题；已回答后移走或改写>
- <剩余未决项需标明 blocking / important / optional>

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
- <内容 2>

### Out of scope

- <看起来相近，但本次明确不做的内容 1>
- <扩展扫视后决定不进本次 PRD scope 的内容>

## 关键场景 / 用户流 / 系统流

### 场景 1 — <名称>

- 触发:
- 预期行为:
- 成功判定:
- 备注 / 来源: [SRC-...]

### 场景 2 — <名称>

- 触发:
- 预期行为:
- 成功判定:
- 备注 / 来源: [SRC-...]

### 边界 / 异常场景

- <边界场景 1>
- <异常场景 2>

## 交付物清单

- <接口 / 页面 / 模块 / 脚本 / 配置 / 数据变更>
- <交付物 2>

## Package artifacts（按需）

<!--
当需求包含承重数据模型、第三方协议、OpenAPI、状态机、事件 payload 或权限矩阵时，可在 `.arbor/tasks/<package>/artifacts/` 放 PRD-stage design artifact，并在这里引用。
Artifact 是 PRD 附属 contract，不是生产实现事实源；impl 不应静默偏离，若需改变则记录 amendment 或 NEEDS_CONTEXT。

常见 artifact：
- 数据 / schema 草案，如 `artifacts/data-model.sql`、`artifacts/feature-schema.json`、`artifacts/save-format.proto`。
- 协议 / 集成 contract，如 `artifacts/integration-contract.md`、`artifacts/api-contract.md`、`artifacts/wire-protocol.md`。
- 状态机、权限矩阵、事件 payload 或验收 golden fixture。
-->

- <如无承重 artifact，写 N/A；如有，列路径和用途>

## Technical Framing

<!-- 
PRD 必须收敛承重技术边界，避免 impl 在关键架构问题上自由发挥。未知项放 Open Questions；不需要项明确 N/A。
新项目：记录技术选型和架构边界。
存量项目：基于代码分析，记录现有结构和变更方案——涉及的现有表/模块、新建/修改的表（含关键字段）、接入现有模式的方式、不能动的边界。
-->

- Existing stack / framework:
- Auth / permissions:
- Module / service boundaries:
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
- 数据/schema：<涉及数据结构、表、文件格式、模型输入输出或 migration 时写；标注 [new]/[existing]；可指向 artifacts/>
- 代码锚点：<涉及模块、文件、接口、页面、命令、子系统或 pipeline 时写；标注 [new]/[existing]>
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
- <约束 2>

## 数据 / 接口备注（按需）

### 数据 / 状态

<!-- 
新项目：列出需要的数据实体、状态结构、文件格式或模型输入输出；结构较多时放入 artifacts/ 并在这里引用。
存量项目：列出涉及的现有数据结构（标注 [existing]）和新增结构（标注 [new]）及关键变更；完整 schema / contract 放入 artifacts/ 或引用现有 source。
-->
- <涉及的状态、表、缓存、队列、幂等键等>

### 接口 / 集成

- 上游:
- 下游:
- 配置 / 环境:

## 验证重点

- <必须验证的行为 1>
- <必须覆盖的失败路径 2>
- <必须确认的可观测性 / 数据状态 3>

## 风险 / 开放问题 / 假设

### Open questions

- <会影响 impl/review 的未决项；PRD 定稿前 blocking 项必须解决>

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
| SRC-RES-001 | research-note | `.arbor/research/.../notes/...md` | <title> | <why> |
| SRC-LOCAL-001 | local-file | `src/...:12-48` | <title> | <why> |
| SRC-EXT-001 | external-url | `https://...` | <title> | <why> |

<!--
═══ 自检清单 (Finalize 前逐项确认, 确认后删除本块) ═══
- [ ] PRD draft 已在 brainstorm 开始时创建或定位，并在每轮用户回答后更新
- [ ] What I already know / Requirements (evolving) / Acceptance Criteria (evolving) / Open Questions / Interview Log 足以支持断点续作
- [ ] Interview Log 只保留关键问答和需求变化，没有完整聊天流水
- [ ] 背景说明了“为什么现在做”
- [ ] In scope / Out of scope 足够明确，且扩展扫视结果已分别归入本次 PRD scope 或 Out of scope
- [ ] 至少写出 2 个关键场景（如适用）
- [ ] Technical Framing 覆盖 stack/auth/frontend-backend/data/admin/integration/testing/migration 等承重边界；N/A 项已明确
- [ ] 如存在承重数据模型、协议、API 或权限矩阵，已在 Package artifacts 引用对应 artifact；否则明确 N/A
- [ ] Acceptance Criteria 覆盖核心路径和关键失败 / 边界路径
- [ ] Boundary decision 已明确为 fits_package，且当前 package 可作为需求/执行/评审/回滚边界
- [ ] Slices 已写好，顺序体现依赖；每个 slice 包含 完成标志；涉及数据/代码/测试的 slice 按实际范围标注 数据/schema、代码锚点、测试（不涉及整条省略，不写 N/A）
- [ ] Slices 只定义需求和顺序，impl 进度通过 `sdd-arbor mark-slice` 写入 `task.json`
- [ ] Open questions / Assumptions / Risks 已分开；blocking / important assumptions 已审计来源、影响和处理方式
- [ ] Sources 能覆盖关键判断，不只是装饰附录
- [ ] 用户已确认最终摘要
- [ ] finalize 只通过 sdd-arbor finalize-brainstorm 写入 ready package
- [ ] 若这是 amendment，旧需求没有被静默改写，AMD-xxx 写清 wrong/correct/affects
- [ ] 若进入 impl，不会因缺少关键信息而立刻卡住
════════════════════════════════════════════════════ -->
