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

当用户没有显式提供 package name，由 brainstorm 从需求标题生成 package name 时，默认使用 Trellis-style 日期前缀：`MM-DD-<topic-slug>`。

- 示例：用户说"知识付费系统" → `.arbor/tasks/05-02-knowledge-paid-system/`。
- `<topic-slug>` 使用英文 lowercase kebab-case；避免中文、空格、下划线和路径分隔符。
- 用户显式给出合法 package name 时优先使用用户给定名称。
- 同日同主题已有 package 时，追加更具体的短后缀，不覆盖旧 package。

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
10. 达到 PRD 定稿条件前，执行一次 PRD 收尾整理：把 evolving 内容落入正式 section，填实背景、目标、In scope、Out of scope、关键场景、交付物、Technical Framing、Slices、验证重点和风险；删除模板示例、占位符和空 section；顶层 `Open Questions` 必须为空或只保留明确标注为 non-blocking 的项。
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
- Data model / persistence：新增/修改状态、表、缓存、迁移、幂等要求。
- Admin / ops surface：管理后台、配置、观测、回滚入口。
- External integrations：第三方、队列、支付、邮件、AI API 等边界。
- Testing strategy：用 `AskUserQuestion` 让用户选择测试策略档位，然后据此确定覆盖范围和 slice 规划：
  - **核心路径测试**（推荐多数项目）：业务逻辑层的关键路径 + 边界 case；外部依赖用 mock/fake。
  - **TDD 驱动**（高可靠要求）：先写测试再写实现，覆盖所有业务逻辑层；外部依赖用 mock/fake。
  - **最小验收**（快速原型）：只测 happy path，确认功能跑通。
  - 无论哪档，外部依赖（支付回调、第三方 API）一律通过 mock/fake 隔离，测试的是"收到响应后的业务逻辑"，不是真实调用。
- Migration / rollout / rollback：上线、迁移和回退边界；不需要则写 N/A。

## Slices

PRD 定稿时必须包含 `## Slices` 段，将需求按实现顺序切成有序的实现切片。Slices 是 brainstorm 的产物——此时细节最多，切片最精准。

Slices 的原则：

- 每个 slice 是一个有意义的实现阶段，不是按文件/函数机械拆分。
- 顺序反映依赖关系：先基建，再核心逻辑，再边缘功能，最后验收。
- 粒度由可验证性决定，不由数量限制决定：每个 slice 完成后应该能用一两句话说清楚"怎么验证它做对了"。如果一个 slice 需要列举 5 个以上独立功能才能描述清楚，它就太粗了，应该拆开。slice 数量没有上限，完全取决于需求本身的复杂度。
- 每个 slice 一行描述，点明目标和关键交付，不需要展开成完整子 PRD。
- 存量项目的 slice 应包含技术锚点——涉及的表、模块、接入方式等，让 impl 知道在现有代码的哪里动刀。新项目不强制。
- 用 `- S-NNN: 描述` 格式列出。Impl 的进度记录在 `task.json` 的 `slices` 数组中，PRD 里的 Slices 段只定义需求，不做进度标记。

存量项目示例（小需求，slice 带技术锚点）：

```markdown
## Slices

- S-001: 小红书渠道适配器 — 新建 XiaohongshuAdapter 继承 ChannelAdapter，channels 表加 type='xiaohongshu'，复用 MessageRouter 分发
- S-002: Webhook 接入 — 新增 /webhooks/xiaohongshu 路由，签名验证，消息体解析转 UnifiedMessage 格式
- S-003: 后台渠道配置 — ChannelConfigPage 新增小红书类型表单，channel_configs 表存 app_id/secret/webhook_url
- S-004: 验收 — 模拟 webhook 消息、自动回复、后台配置，边界 case（签名失败、重复消息幂等）
```

存量项目示例（大需求，slice 同样带技术锚点）：

```markdown
## Slices

- S-001: 多租户数据隔离 — tenants 表 [new]，现有 users/orders/products 表加 tenant_id [existing]，TenantScope 全局查询作用域
- S-002: 租户认证与切换 — 租户登录入口，JWT payload 加 tenant_id，中间件校验租户归属
- S-003: 租户管理后台 — 超管视角的租户 CRUD，租户状态（启用/禁用/过期），关联套餐
- S-004: 套餐与功能开关 — plans 表 [new]，plan_features 表 [new]，FeatureGate 中间件按租户套餐控制 API 访问
- S-005: 现有业务适配 — ProductController/OrderController 等加 TenantScope，确认管理后台筛选器、导出、统计按租户隔离
- S-006: 数据迁移 — 存量数据归属默认租户，迁移脚本回填 tenant_id，校验无孤立记录
- S-007: 验收 — 租户 A/B 数据完全隔离、跨租户访问拒绝、套餐功能开关生效、存量数据迁移后业务正常
```

新项目示例（不强制技术锚点）：

```markdown
## Slices

- S-001: 项目基建 — Laravel + React TS 脚手架、DB config、健康检查 API、dev 启动命令
- S-002: 认证 — 学员注册登录、管理员登录、路由守卫、token 管理
- S-003: 内容数据模型与 API — 统一内容/章节/分类模型、CRUD API、访问类型标记
- S-004: 订单与权限模型 — 订单创建、模拟支付确认、单课授权、会员有效期开通
- S-005: 后台内容管理 — 课程/专栏列表、创建/编辑、章节管理、上下架
- S-006: 后台订单与用户 — 订单列表、模拟支付确认、用户/会员状态查看
- S-007: 后台工作台与看板 — 基础数据卡片、最近订单/内容概览
- S-008: 前台首页与列表 — 首页布局、课程/专栏列表、分类筛选、价格/类型展示
- S-009: 前台详情与购买 — 详情页、购买/开会员 CTA、模拟支付流程、权限提示
- S-010: 学习中心 — 视频/图文学习页、章节目录、进度记录、收藏
- S-011: 我的课程/会员 — 已购内容、继续学习入口、会员状态、收藏列表
- S-012: 验收与边界自检 — 核心购买学习路径、未授权/过期/下架/异常 URL 等边界
```

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
- PRD 不再残留 `<...>` 模板占位符、示例 source、空 section；`背景与问题`、`目标`、`本次范围`、`关键场景`、`交付物清单`、`Technical Framing`、`Slices`、`验证重点` 都必须是可执行内容。
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
