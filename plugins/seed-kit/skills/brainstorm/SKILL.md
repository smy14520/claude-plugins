---
name: brainstorm
description: "把模糊想法收敛成可执行的 PRD。访谈式提问（一次一个高价值问题 + 推荐答案），终点是 .arbor/tasks/<task>/prd.md：可证伪 AC + 有序 Slices（每 slice 声明验证命令）。"
---
# Brainstorm — 需求收敛访谈

通用约定见 [`../references/conventions.md`](../references/conventions.md)。

把一个模糊想法收敛成可执行的 PRD。从零开始的项目要引导用户做关键决策（选型、形态、范围）；已有项目要先读代码、CLAUDE.md 理解现状与既有模式，只对**直接影响本任务**的问题提改进，并问边界与接缝。

## 访谈循环

持续追问，直到对目标、边界、依赖和验收标准达成共同理解：

- 沿决策树推进：先解决会影响后续选择的前置决策（产品形态 → 技术选型 → 范围边界 → 验收标准）。
- 对有用户可感面的产品（UI/CLI/文案/API DX），收敛**质量基线**：参考产品、设计语言、“感觉像 X”、明确不要的样子。用参考而非清单——参考传递丰富先验，让 impl 在地板之上发挥，而不是重新发明品味。
- 一次只问一个问题；每个问题给出你的推荐答案和理由，让用户判断/修正。
- 能从仓库代码确认的事实先自行查证，不要问用户。
- **易过期事实**（版本号、发布日期、最新 API、依赖兼容性、弃用状态）——推荐前先通过 WebSearch/WebFetch 查官方源（releases、官方文档、changelog）的**当前值**，不靠回忆。这是"不主动搜索"的唯一例外：只查单个易过期事实，不开 research 主题。进 PRD 时这类事实带 `查证于 <日期>（<来源>）` 标注，例如 `Laravel 13.x（查证于 2026-06-15，laravel.com/releases）`。架构概念、语法、原理等非易过期事实照常靠记忆。
- 只有用户明确指定时才读 `.arbor/research/<topic>/` 或查 `.wiki/`；不主动搜索。

## 产出 PRD

用户确认收敛结果后：

1. `seed new <task>` 创建任务目录。
2. 按模板填写 `prd.md`：
   - **需求与验收标准**：每条 AC 可证伪（Given/When/Then，至少一条失败路径），写需求的同时写预期证据。
   - **Technical Framing**：轻量——选型、模块边界、与现有代码的接缝、明确不做什么。
   - **质量基线（体验意图）**：产品有用户可感面时写参考级目标（参考产品、设计语言、质量门槛、明确不要的样子），不是功能清单；无可感面可省略。
   - **Slices**：有序最小可验证步，prd.md 里只写索引行 `### [ ] S-NNN 标题`。
3. 每个 slice 写一个 `slices/S-NNN.md`（标题与索引行一致）：
   - `## 交付面` 声明本 slice 实际交付的面（参考词汇表 backend-domain、api、web-ui、e2e、compliance、infra，项目可扩展，定义见 conventions）。
   - `## 验收` 写对应 AC 与细节。
   - `## 验证面` 至少一条验证项，每条 `[kind][surface] <obligation-id>: <可观测行为>`（obligation-id 可带 `AC-N` 作 review 对账线索；命令不写在这里，impl 用 `run-check --obligation <id>` 绑定）。
   - **验证项设计规则见 conventions**（覆盖、kind、烟雾、AC 维度）——这里只写 slice 形状，不重述。仅记两条：human 不能替代可断言交付面；**设验证面前先读项目的 `.claude/rules/`（测试纪律，决定 web-ui 用交互 assert 还是 judge）与 `DESIGN.md`（品味）**，项目无则用通用地板。
   - 有可感面时，质量基线 + `DESIGN.md` 定体验意图。
4. `seed status <task>` 校验结构通过（有结构错误必须修复）。

slice 拆分由你推荐、用户拍板；不强制最小切片，也不要为了显得完整而拆假边界。

## 修改既有 PRD

需求变化时直接编辑 prd.md 与对应的 `slices/S-NNN.md`（不动 checkbox），并在 `## 变更记录` 追加一行：日期 + 改了什么 + 为什么。

## 停止

PRD 写好并通过 `seed status` 校验后停止，告知用户可以用 impl 执行。不自动进入 impl。
