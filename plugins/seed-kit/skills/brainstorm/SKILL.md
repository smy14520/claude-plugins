---
name: brainstorm
description: "把模糊想法收敛成可执行的 PRD。访谈式提问（一次一个高价值问题 + 推荐答案），终点是 .arbor/tasks/<task>/prd.md：可证伪 AC + 有序 Slices（每 slice 声明验证命令）。"
---
# Brainstorm — 需求收敛访谈

通用约定见 [`../references/conventions.md`](../references/conventions.md)。

把一个模糊想法收敛成可执行的 PRD。从 0 的项目要引导用户做关键决策（选型、形态、范围）；已有项目要先读代码理解现状，再问边界与接缝。

## 访谈循环

持续追问，直到对目标、边界、依赖和验收标准达成共同理解：

- 沿决策树推进：先解决会影响后续选择的前置决策（产品形态 → 技术选型 → 范围边界 → 验收标准）。
- 一次只问一个问题；每个问题给出你的推荐答案和理由，让用户判断/修正。
- 能从仓库代码确认的事实先自行查证，不要问用户。
- **易过期事实**——版本号、发布日期、最新 API、依赖兼容性、弃用状态——推荐前用 WebSearch/WebFetch 查官方源（releases / 官方文档 / changelog）的**当前值**，不靠回忆；这是"不自己去搜"的**窄例外**：只点查单个易过期事实，不开 research 主题。进 PRD 时这类事实带 `查证于 <日期>（<来源>）` 标注，例如 `Laravel 13.x（查证于 2026-06-15，laravel.com/releases）`。架构概念、语法、原理等非易过期事实照常靠记忆。
- 只有用户明确指定时才读 `.arbor/research/<topic>/` 或查 `.wiki/`；不要自己去搜。

## 产出 PRD

用户确认收敛结果后：

1. `seed new <task>` 创建任务目录。
2. 按模板填写 `prd.md`：
   - **需求与验收标准**：每条 AC 可证伪（Given/When/Then，至少一条失败路径），写需求的同时写预期证据。
   - **Technical Framing**：轻量——选型、模块边界、与现有代码的接缝、明确不做什么。
   - **Slices**：有序最小可验证步，prd.md 里只写索引行 `### [ ] S-NNN 标题`。
3. 每个 slice 写一个 `slices/S-NNN.md`（标题与索引行一致）：`## 交付面` 先声明本 slice 实际交付的面（闭集见 conventions）；`## 验收` 写对应 AC 与细节；`## 验证面` 至少一条验证项，每条写成 `[kind][surface] target`。
   - **覆盖全部交付面**：`## 验证面` 必须覆盖 `## 交付面` 的每一项；backend-domain / api / e2e / infra 需要 assert，web-ui 可 assert 或 judge，compliance 才可 human。human 不能替代可断言的交付面。
   - **assert 优先**：优先写**会失败的断言**——后端逻辑交给测试套件（`php artisan test`/`pytest`/`vitest`），API 流写成一个**自包含**的集成测试（内部自己 setup→act→assert），不要写一串跨命令、靠 shell 变量串状态的 curl。第三方/不可达边界用**录制好的 fixture / 契约**断言，不要静默跳过。
   - **judge**：难以机械断言的语义/UI 行为用 `[judge][web-ui]`，注明 rubric 位置；由独立 agent 在 fresh session 裁决。
   - **human**：真正的涉众签收，仅用于合规/备案等本质不可自动化的 `[human][compliance]`。**testability gate**：一个 slice 如果只能 human 验证，是设计气味——显式标出来并写明为什么无法 assert/judge，让用户判断是接受还是改设计。
   - **覆盖 AC 的每个维度**：slice 的验证要真的触及它 AC 声称的每个方面，别让一条线的通过冒充另一条线的覆盖（例：AC 含"正确路径 + 失败路径 + 边界"，验证只测了正确路径，不能说整体已验证）。某维度不确定怎么验证时补 judge/human，不要默默漏掉。
   assert 的命令要写成 impl 时能原样执行、且功能错了真的会失败的形式。
4. `seed status <task>` 校验结构通过（有结构错误必须修复）。

slice 拆分由你推荐、用户拍板；不强制最小切片，也不要为了显得完整而拆假边界。

## 修改既有 PRD

需求变化时直接编辑 prd.md 与对应的 `slices/S-NNN.md`（不动 checkbox），并在 `## 变更记录` 追加一行：日期 + 改了什么 + 为什么。

## 停止

PRD 写好并通过 `seed status` 校验后停止，告知用户可以用 impl 执行。不自动进入 impl。
