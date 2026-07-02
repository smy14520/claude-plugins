---
name: brainstorm
description: "把模糊想法收敛成可执行的 PRD。访谈式提问——用 AskUserQuestion 一次问一个高价值问题（推荐项置首、用户可改/另填），终点是 .arbor/tasks/<task>/prd.md：可证伪 AC + 有序 Slices。"
---
# Brainstorm — 需求收敛访谈

> 调用名：`seed-kit:brainstorm`（全名见 conventions.md 登记表，别加 `seed-` 前缀）。

通用约定见 [`../references/conventions.md`](../references/conventions.md)；验证设计（三类 kind / judge / rubric / 硬规则）见 [`../references/verification.md`](../references/verification.md)。

把一个模糊想法收敛成可执行的 PRD。从零开始的项目要引导用户做关键决策（选型、形态、范围）；已有项目要先读代码、CLAUDE.md 理解现状与既有模式，只对**直接影响本任务**的问题提改进，并问边界与接缝。

## 访谈循环

持续追问，直到对目标、边界、依赖和验收标准达成共同理解：

- 沿决策树推进：先解决会影响后续选择的前置决策（产品形态 → 技术栈 → 范围边界 → 验收标准）。
- 对有用户可感面的产品（UI/CLI/文案/API DX），了解期望的体验方向：参考产品、设计语言、"感觉像 X"、明确不要的样子。用参考而非清单——参考传递丰富先验，让 impl 发挥判断力。这些自然写入 Goal 和验收条目中，不独立成段。
- **提问通道看场景**：人在环上（真实交互）用 **AskUserQuestion 工具**——`questions` 只放一条（一次一题），2–4 个选项，推荐项置首、label 带"(推荐)"，取舍写进各选项 description；开放题也走选项（用户可选 Other 自由输入）。**脚本化 / 无交互驱动**（如自动化测试 harness）改用**纯文本散文一次一题**——不要调用 AskUserQuestion（驱动端无法回答菜单，会卡死）。
- 能从仓库代码确认的事实先自行查证，不要问用户。
- **易过期事实**（版本号、发布日期、最新 API、依赖兼容性、弃用状态）——推荐前先通过 WebSearch/WebFetch 查官方源（releases、官方文档、changelog）的**当前值**，不靠回忆。这是"不主动搜索"的唯一例外：只查单个易过期事实，不开 research 主题。进 PRD 时这类事实带 `查证于 <日期>（<来源>）` 标注，例如 `Laravel 13.x（查证于 2026-06-15，laravel.com/releases）`。架构概念、语法、原理等非易过期事实照常靠记忆。
- 只有用户明确指定时才读 `.arbor/research/<topic>/` 或查 `.wiki/`；不主动搜索。

## 产出 PRD

用户确认收敛结果后：

1. `seed new <task>` 创建任务目录。
2. 按模板填写 `prd.md`（Goal + Acceptance Criteria + Out of Scope）：
   - **Goal**：一段话概述——这是什么、为什么做。有可感面时，期望的体验方向（参考产品、设计语言、"感觉像 X"）自然融入。
   - **Acceptance Criteria**：有序 slice（`### [ ] S-NNN 标题`），每个 slice 下用 `* [ ]` 写验收条目。一个 `* [ ]` 一个测试用例——正向一条、反向一条、边界一条。技术决策融入相关条目，不独立成段。
   - **Out of Scope**：明确不做什么。
   - 不再创建单独 slice 文件——所有 slice 内容直接在 prd.md 的 `### [ ] S-NNN` heading 下写。
4. `seed status <task>` 校验结构通过（有结构错误必须修复）。

slice 拆分由你推荐、用户拍板；不强制最小切片，也不要为了显得完整而拆假边界。

## 修改既有 PRD

需求变化时直接编辑 prd.md（不动 checkbox）。

## 停止

PRD 写好并通过 `seed status` 校验后停止。建议用户先跑 `/seed-kit:review-prd`（独立审查 PRD + 读代码对账），再进 impl。由用户决定是否触发 review-prd，不自动进入 impl。
