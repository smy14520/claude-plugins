---
name: brainstorm
description: "把模糊需求持续沉淀到 sdd-kit package PRD draft，断点续作访谈，最终收敛成 PRD-first package。支持 normal 和 grill-me；不要用于 research、impl 或 review。"
---

# Brainstorm — durable PRD-first package

使用语言：中文。

Arbor helper 入口、路径和常用命令见 [`../references/arbor-helper.md`](../references/arbor-helper.md)；运行前遵守其中约定。

Brainstorm 把需求变成可执行 package PRD：先创建或定位 `.arbor/tasks/<package>/prd.md` draft，把每轮访谈结果写进 PRD；等需求、technical framing、验收和边界足够清楚并得到用户确认后，通过 `sdd-arbor finalize-brainstorm` 写入 ready package。它不写代码、不 review、不维护第二套执行计划。

## 模式

- `normal`：高效收敛。使用 `references/normal.md` 的 pacing 和 turn shape；已有信息足够时尽快整理 PRD 并定稿。
- `grill-me`：高强度需求追问。使用 `references/grill-me.md` 的 pacing 和 turn shape，持续追问直到目标、边界、关键场景、technical framing 和验收口径足够清楚，再整理 PRD 并定稿。

### 模式选择

1. 用户显式指定 `normal` / `grill-me` / 直接定稿 / 不追问时，遵从用户。
2. 用户明确要求直接创建 package 或定稿时，不为了模式选择打断；若存在 blocking 缺口，只问一个最高价值问题。
3. 用户没有指定模式，且输入是模糊、产品型、系统型、方案型需求，或存在多个合理方向 / 关键取舍 / 验收不明时，必须调用 `AskUserQuestion` 询问 `normal` / `grill-me`；"知识付费系统"这类产品型需求属于这个分支。
4. 用户没有指定模式，且当前是 research 之后进入 brainstorm，也必须调用 `AskUserQuestion`，除非用户明确要求直接定稿；research 是上下文，不是需求冻结。
5. 只有当需求已经包含目标、范围、关键场景、验收、非目标和技术边界，且用户明显期待推进时，才可以默认 `normal` 而不弹模式选择。

`AskUserQuestion` 选项固定为：

- `grill-me`：一轮一个问题，高强度追问目标、边界、关键场景、technical framing、验收和取舍；产品 / 系统 / 商业模式不清时默认推荐。
- `normal`：基于已有信息快速收敛 PRD，只在 blocking 缺口上问一个问题；需求基本清楚时推荐。

## Package naming

用户显式给名时优先使用。否则用 `MM-DD-<topic-slug>`（lowercase kebab-case，避免中文/空格/路径分隔符）；示例："知识付费系统" → `05-02-knowledge-paid-system`。同日同主题已有 package 时追加更具体后缀，不覆盖旧 package。

## Draft PRD workspace

Brainstorm 一开始就要创建或定位 active draft：`.arbor/tasks/<package>/prd.md`。

- 新需求：生成 package name，调用 `sdd-arbor create <package>` 创建 `.arbor/tasks/<package>/`，用 PRD 模板 seed `prd.md`，frontmatter `status: draft`。
- 续作：用户显式给 package name 时，读取对应 `.arbor/tasks/<package>/prd.md`。
- 自然语言续作：用户只说 topic / "继续某需求"时，扫描 `.arbor/tasks/*/prd.md` 的 frontmatter、标题、`What I already know`、`Open Questions`，找到候选后继续；多个候选时只问一次确认。
- Draft package 只是访谈工作区，不等于 ready package；不要手写 package control state。
- PRD draft 是 source of truth：每轮回答后先更新 PRD，再问下一个问题。

## Research handoff

Research 资料只是 source-backed context / 候选理解，不代表需求已经被用户确认或冻结。

从 research 进入 brainstorm 时：

1. 定位与当前需求相关的 research topic。用户显式指定 topic 时直接用；未指定时扫描 `.arbor/research/*/index.md` 的标题和摘要，匹配当前需求，多个候选时用 `AskUserQuestion` 让用户确认。只读匹配的 topic，不遍历全部 research。
2. 读取该 topic 的 `index.md`、相关 notes、open questions 和 readiness。
2. 显式区分 research 已支持的事实、research 提出的候选方向、仍未由用户确认的产品 / 范围 / 验收 / 技术 framing 假设。
3. `ready-for-brainstorm` 只表示资料足够让 brainstorm 接手，不表示需求已定稿。
4. 除非用户明确指定 `normal` 或直接定稿，否则用 `AskUserQuestion` 让用户选择模式。
5. 如果 research 中仍有 open questions、关键 assumptions、多个可行方向，默认推荐 `grill-me`。

## Question interaction rules

- 每轮只问一个最高价值问题。
- 产品形态、范围、权限、计费、数据模型、技术边界等离散取舍必须用 `AskUserQuestion` 给 2-4 个选项，推荐项放第一，并在推荐项 description 中说明推荐理由。
- 真正开放题才用文字给推荐答案和理由。
- 用户回答后必须先更新 PRD draft，再继续下一问。

## 用户自带规格

用户可能主动提供技术规格作为 PRD 的硬约束：SQL / 表结构定义、API 文档、接口契约、参考设计、架构图说明等。

处理方式：

- 用户提供的规格写入 PRD 对应 section 作为基准约束（SQL 写入数据备注，API 文档写入 Technical Framing 或接口备注），不需要通过 grill-me 重新推导。
- 写入后仍然审视规格的技术合理性（缺索引、字段类型、命名一致性、与现有结构的兼容性等）。发现问题时用 `AskUserQuestion` 提出具体建议，由用户决定是否采纳。用户确认后的版本才是最终约束。
- 仍然用 grill-me 追问规格之外的未决问题（产品边界、验收标准、规格中未覆盖的技术决策）。
- 如果用户提供的规格与代码分析存在冲突，用 `AskUserQuestion` 确认以哪个为准。

## 工作循环

1. 读取用户输入、用户提供的规格、相关代码、已有 research / PRD。
2. 创建或定位 `.arbor/tasks/<package>/prd.md` draft；如果是新 draft，立即写入已知背景、初始 open questions 和当前推荐方向。
3. 按模式选择规则决定是否先用 `AskUserQuestion` 询问 `normal` / `grill-me`。
4. 简短说明当前理解和真正阻塞 finalize 的缺口。
5. 若仍不清楚：按 Question interaction rules 提问；停止等待用户。
6. 用户回答后：必须先更新 PRD draft，再继续。更新内容包括：
   - 将已回答问题从 `Open Questions` 移走或改写为新的未决问题。
   - 追加 / 调整 `Requirements (evolving)`、`Acceptance Criteria (evolving)` 和 `Technical Framing`。
   - 把关键问答和需求变化追加到 `Interview Log`；只记关键问题、用户选择/回答、产生的需求变化，不保存完整聊天流水。
7. PRD 更新完成后，再问下一个最高价值问题；重复这个循环直到形成初步 package scope 轮廓。
8. 初步 package scope 轮廓形成后，执行一次扩展扫视；完成后回到收敛。
9. 进入收尾前先处理 PRD 里的 `Open Questions`：
   - 会改变本次交付 scope、数据模型、权限、接口、测试或验收的，是 blocking question，下一轮必须优先追问。
   - 不影响本次实现的，移入 Out of scope / Risks / Assumptions，并写清处理方式；不要继续留在顶层 `Open Questions` 阻塞 finalize。
10. 达到 PRD 定稿条件前，执行一次 PRD 收尾整理：把 evolving 内容落入正式 section，填实背景、目标、In scope、Out of scope、关键场景、交付物、Package artifacts、Technical Framing、Slices、验证重点和风险；删除模板示例、占位符和空 section；顶层 `Open Questions` 必须为空或只保留明确标注为 non-blocking 的项。
11. 收尾整理完成后，先自检 PRD：不得残留 `<...>`、示例 `SRC-LOCAL-001`、示例 slice、空的正式 section，且 Slices 必须是针对当前 PRD 的可执行切片。自检不通过时继续编辑 PRD，不要询问用户确认定稿。
12. 自检通过后，给用户最终摘要并请求确认；用户确认后调用 `sdd-arbor finalize-brainstorm`。
13. 停在 impl 前，告诉用户下一步用 impl 执行。

## Context first

Brainstorm 开始时先判断项目上下文：

- **新项目**（无既有代码/数据库）：按常规工作循环进行。
- **存量项目**（已有代码、表结构、业务模块）：在第一轮追问前，主动读取与需求相关的现有代码，分析涉及的表结构、模块设计、接口模式和扩展点，将分析结论写入 PRD 的 `What I already know` 和 `Technical Framing`。

存量项目的技术分析至少覆盖：

- 涉及的现有表和关键字段
- 现有模块/类的设计模式（适配器、策略、事件等）
- 新需求的接入点：改哪些表/模块，建哪些新表/模块
- 不能动的边界：其他模块依赖的接口、共享表等

分析结论侧重变更方案（改什么、建什么、怎么接入），现有结构只需点明涉及的表/模块和关键关系，不需要完整复述。

## Technical Framing

产品 PRD 必须收敛承重技术边界，避免 impl 在关键架构问题上自由发挥。不要把它写成实现步骤流水账；只记录会改变 scope、验收或风险的决定。

Finalize 前至少覆盖：

- Existing stack / framework：沿用什么、不能引入什么。
- Auth / permissions：谁能做什么，权限边界在哪里。
- Frontend / backend boundary：页面、API、service、CLI 或脚本边界。
- Data model / persistence：新增/修改状态、表、缓存、迁移、幂等要求；字段/关系较多时使用 package artifact（如 `artifacts/data-model.sql`）承载草案级 schema contract。
- Admin / ops surface：管理后台、配置、观测、回滚入口。
- External integrations：第三方、队列、支付、邮件、AI API 等边界。
- Testing strategy：用 `AskUserQuestion` 让用户选择测试策略档位，然后据此确定覆盖范围和 slice 规划：
  - **核心路径测试**（推荐多数项目）：业务逻辑层的关键路径 + 边界 case；外部依赖用 mock/fake。
  - **TDD 驱动**（高可靠要求）：先写测试再写实现，覆盖所有业务逻辑层；外部依赖用 mock/fake。
  - **最小验收**（快速原型）：只测 happy path，确认功能跑通。
  - 无论哪档，外部依赖（支付回调、第三方 API）一律通过 mock/fake 隔离，测试的是"收到响应后的业务逻辑"，不是真实调用。
- Migration / rollout / rollback：上线、迁移和回退边界；不需要则写 N/A。

## Package artifacts

当需求包含非平凡数据模型、第三方协议、OpenAPI、状态机、事件 payload 或权限矩阵时，在 `.arbor/tasks/<package>/artifacts/` 写 package-local design artifact，并在 PRD 的 `Package artifacts` / `数据 / 接口备注` / `Sources` 中引用。

- Artifact 是 PRD 附属 contract，不是生产实现事实源。
- 新项目可用 `artifacts/data-model.sql` 压实草案级 schema contract；impl 后最终事实源是代码里的 migration/schema。
- 第三方集成可用 `artifacts/integration-contract.md` 记录 payload、验签、token、mock/real 边界。
- 不要把大段 SQL / 协议正文塞进 slice；slice 只引用 artifact 中的实体、协议或 contract。
- 若 impl/review 发现 artifact 错误或需要改变，走 amendment / NEEDS_CONTEXT，不静默偏离。

## Slices

PRD 定稿时必须包含 `## Slices` 段，按依赖顺序写出有序实现切片。Slices 是 brainstorm 的产物——此时细节最多，切片最精准。

每个 slice 用 `### S-NNN: <标题>` 起头，body 用 `- 字段：值` 形式给出。字段按需出现——**slice 涉及就写，不涉及就整条省略**，不写 N/A、不留占位。不分存量/新项目：是否写某字段只看这个 slice 的实际范围。

**必填**：

- `完成标志`：一句话可验证的 done-condition。每个 slice 都写，没有例外。

**按需**（slice 涉及就写，不涉及整条省略）：

- `数据/schema`：动到表、数据模型、migration 时写。标注 `[new]` / `[existing]`；项目有 `artifacts/data-model.sql` 时指向具体位置。
- `代码锚点`：动到或新建模块、文件、接口、页面时写。标注 `[new]` / `[existing]`；UI、外部集成、权限变更都归此字段。
- `测试`：Testing strategy 为核心路径/TDD 时写（覆盖路径/边界或 test 文件名）；最小验收档可省。

**完成标志 vs Acceptance Criteria**：AC（PRD 顶层 `## Acceptance Criteria`）是**用户视角**的整体验收（"能创建账户并查看月度统计"）；完成标志是每 slice 的**技术视角** done-condition（"账户 API 返回 201，DB 记录已写入"）。定稿时每条 AC 应能追溯到 1 个或多个 slice 的完成标志组合。

**粒度**由可验证性决定：完成后能用一两句话说清楚"怎么验证"。一个 slice 需要列举 5 个以上独立功能才能描述清楚就太粗，应该拆。slice 数量没有上限。顺序反映依赖：先基建，再核心，再边缘，最后验收。

Impl 进度记录在 `task.json.slices` 数组（通过 `sdd-arbor mark-slice` 更新），PRD 里的 Slices 段只定义需求，不做进度标记。

示例（同一套 schema 涵盖不同 slice 类型）：

```markdown
## Slices

### S-001: 多租户数据隔离基础

- 完成标志：现有 users/orders/products 表查询自动按 tenant_id 过滤；跨租户查询返回空
- 数据/schema：tenants 表 [new]；users/orders/products 加 tenant_id [existing]；migration 20260505_add_tenant_id.sql
- 代码锚点：TenantScope [new] src/scopes/tenant.ts；QueryBuilder 钩子 [existing] src/db/query-builder.ts
- 测试：tenant-scope.test.ts 覆盖 基础隔离 / 跨租户拒绝 / 空租户降级

### S-002: 账户管理页面

- 完成标志：能创建、编辑、删除账户并同步刷新列表
- 代码锚点：src/pages/accounts/* [new]；src/api/accounts.ts [existing]
- 测试：accounts-page.test.tsx 覆盖 CRUD 流程 + 空态

### S-003: 项目基建

- 完成标志：`npm run dev` 启动后健康检查 API 返回 200
```

S-001 涉及数据、代码、测试三字段都写；S-002 是纯 UI 没动数据层，所以省 `数据/schema`；S-003 是基建，只有完成标志。字段由 slice 实际涉及范围决定，不由项目类型决定。

## 扩展扫视

扩展扫视是 brainstorm 内部的 diverge → converge 转折，不是 research，也不是新阶段。

在初步 package scope 轮廓形成后、PRD 定稿前，简短扫一遍：

- 未来演进：哪些能力很快会被需要，但不一定进本次 PRD scope？
- 相关场景：有没有相邻用户流 / 系统流会影响当前边界？
- 失败与边界：哪些异常、权限、数据、迁移或回滚边界容易漏？

让用户选择：哪些纳入本次 PRD scope，哪些明确写入 `Out of scope`。扫视结果必须写回 `Requirements (evolving)` / `Out of scope` / `Acceptance Criteria (evolving)`，再进入 finalize。

## PRD 定稿条件

只有同时满足以下条件，才可以整理 PRD 并调用 `sdd-arbor finalize-brainstorm`：

- Blocking questions 已解决，剩余 open questions 不阻塞 impl/review。
- Technical Framing 已覆盖承重技术边界；未知承重项不能留给 impl 猜。
- 扩展扫视已完成，结果已写入 Requirements / Out of scope / Acceptance Criteria。
- Acceptance Criteria 覆盖核心路径和关键失败 / 边界路径。
- Slices 已写好，按依赖顺序列出当前 PRD 的实现切片；不能保留示例 slice 或 `<...>`。
- PRD 已从 evolving 区整理进正式结构，保留必要决策和来源，避免访谈流水污染最终交付物。
- PRD 不再残留 `<...>` 模板占位符、示例 source、空 section；`背景与问题`、`目标`、`本次范围`、`关键场景`、`交付物清单`、`Package artifacts`、`Technical Framing`、`Slices`、`验证重点` 都必须是可执行内容。
- 顶层 `Open Questions` 中没有 blocking question；若保留 non-blocking 问题，必须说明为什么不阻塞本次 impl/review。
- 用户确认最终摘要。

Finalize 时调用 `sdd-arbor finalize-brainstorm --input-json '{"name": "<package>", "kind": "single", "prd_path": ".arbor/tasks/<package>/prd.md"}'`。

## Arbor

- Draft 阶段可以创建 / 编辑 `.arbor/tasks/<package>/prd.md`，但不要手写 `.arbor` control state。
- Ready package 必须由 `sdd-arbor finalize-brainstorm --input-json ...` 写入。

## Amendment 入口

当 review 判定 BRAINSTORM_DRIFT 后回到 brainstorm 时：

1. 读取 `task.json` 的 `review_result`，了解 drift 的具体原因。
2. 不重开完整 grill-me 循环。只针对 drift 指出的问题追问确认。
3. 用 PRD 的 `## Amendments / Forward-only corrections` 记录修正，不静默改写已有需求。每条 amendment 用 `AMD-001`、`AMD-002` 编号，写清 wrong/correct/affects/source。
4. 如果 amendment 影响 Slices（新增、删除或重排），同步更新 Slices 段。
5. 修正完成后重新 finalize。

## 不做

- 不采集 raw evidence（用 research）。
- 不写代码（用 impl）。
- 不做语义审计（用 review）。
- 不自动推进下一阶段。
