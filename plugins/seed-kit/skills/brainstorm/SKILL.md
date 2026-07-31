---
name: brainstorm
description: "把模糊想法收敛成可执行的 PRD。访谈式提问——用 AskUserQuestion 一次问一个高价值问题（推荐项置首、用户可改/另填），终点是 .arbor/tasks/<task>/prd.md：可证伪 AC + 有序 Slices。"
---
# Brainstorm — 需求收敛访谈

> 调用名：`seed-kit:brainstorm`（全名见 conventions.md 登记表，别加 `seed-` 前缀）。

通用约定见 [`../references/conventions.md`](../references/conventions.md)；验证设计（三类 kind / judge / rubric / 硬规则）见 [`../references/verification.md`](../references/verification.md)。

把一个模糊想法收敛成可执行的 PRD。从零开始的项目要引导用户做关键决策（选型、形态、范围）；已有项目要先读代码、CLAUDE.md 理解现状与既有模式，只对**直接影响本任务**的问题提改进，并问边界与接缝。

## 访谈循环

持续追问，直到每个会影响实现结果的隐含决策都被拍板，没有重要假设被沉默地默认带过：

- 沿决策树每个分支走到能写出**可证伪验收**的叶子；依赖先于被依赖。还有未拍板的隐含决策时，不产出 PRD。
- 对有用户可感面的产品（UI/CLI/文案/API DX），了解期望的体验方向：参考产品、设计语言、"感觉像 X"、明确不要的样子。用参考而非清单——参考传递丰富先验，让 impl 发挥判断力。这些自然写入 Goal 和验收条目中，不独立成段。
- **提问通道看场景**：人在环上（真实交互）用 **AskUserQuestion 工具**——`questions` 只放一条（一次一题），2–4 个选项，推荐项置首、label 带"(推荐)"，取舍写进各选项 description；开放题也走选项（用户可选 Other 自由输入）。**脚本化 / 无交互驱动**（如自动化测试 harness）改用**纯文本散文一次一题**——不要调用 AskUserQuestion（驱动端无法回答菜单，会卡死）。
- 能从仓库代码确认的事实先自行查证，不要问用户。必要时查看与需求直接相关的近期提交，确认正在演化的接口、边界或约定。
- 只有存在会显著影响范围、接口、成本或后续 slice 的真实分叉时，给 2–3 个可行方向与取舍，推荐项置首。
- 收敛前追问一次隐性期望：用户默认成立但没写出口的期望里，哪些值得写成可证伪条目？值得守的落条目，不值得的显式进 Out of Scope——让"不守"也是决定而非遗漏。**排除是用户的决策**：任何你认为"不值得做"的点，写进 Out of Scope 前必须先问过用户（走本 skill 的提问通道），不能单方拍板。项目标准层（CLAUDE.md / DESIGN.md / .claude/rules）已声明的质量基线，与本任务相关的转译成本任务条目。维度按项目语境判断，不套通用清单。
- **易过期事实**（版本号、发布日期、最新 API、依赖兼容性、弃用状态）——推荐前先通过 WebSearch/WebFetch 查官方源（releases、官方文档、changelog）的**当前值**，不靠回忆。这是"不主动搜索"的唯一例外：只查单个易过期事实，不开 research 主题。进 PRD 时这类事实带 `查证于 <日期>（<来源>）` 标注，例如 `Laravel 13.x（查证于 2026-06-15，laravel.com/releases）`。架构概念、语法、原理等非易过期事实照常靠记忆。
- 入场时跑 `seed wiki index --json` 加载项目记忆——全量索引（title + description + type + area），轻量无负担。访谈过程中扫描索引，自行读取相关的 decision / module / cross_cut 页作为背景上下文。

## 产出 PRD

用户确认收敛结果后：

1. `seed new <task>` 创建任务目录。
2. 按模板填写 `prd.md`（Goal + Acceptance Criteria + Out of Scope）：
   - **Goal**：一段话概述——这是什么、为什么做。有可感面时，期望的体验方向（参考产品、设计语言、"感觉像 X"）自然融入。
   - **Acceptance Criteria**：有序 slice（`### [ ] S-NNN 标题`），每个 slice 下用 `* [ ]` 写验收条目。一个 `* [ ]` 一个测试用例——正向一条、反向一条、边界一条。技术决策融入相关条目，不独立成段。
   - **wiki 知识区分**：精确位置（文件/函数/插入点）直接写进验收条目——这是 task 特定的，没有复利价值。模式/原理/陷阱（"为什么这么设计""这个坑怎么避"）用 `[[../.wiki/页面路径]]` 引用——让 impl 自己去读原文，同一个原理不存两份。
   - **Out of Scope**：明确不做什么。每条排除都必须是用户确认过的决定——访谈中问过的直接落盘，没问过的回提问通道补问一次；写入时末尾带（用户确认）标注（`seed status` 拒绝无标注条目）。
   - 不再创建单独 slice 文件——所有 slice 内容直接在 prd.md 的 `### [ ] S-NNN` heading 下写。
3. PRD 落盘后做一次 inline self-review：清除 TBD/TODO、占位符和模糊语句；核对 Goal、Acceptance Criteria、Out of Scope 是否一致，task 是否过大到应拆成独立 task，以及每条 AC 是否只有一种可执行解释。发现问题直接修当前 PRD，不新增 artifact 或 stage。
4. 自审并修正后，再运行 `seed status <task>` 校验结构（有结构错误必须修复并重跑）。

slice 拆分由你推荐、用户拍板；不强制最小切片，也不要为了显得完整而拆假边界。

## 修改既有 PRD

需求变化时直接编辑 prd.md（不动 checkbox）。

## 停止

PRD 写好并通过 `seed status` 校验后：
- **project-scoped 决策**——以后做其他 task 的人也需要知道的——落 `.arbor/.wiki/decision/` 页；决策融入验收条目的部分已在 PRD 里，不重复。
- **新模块或模块边界变化**落 `.arbor/.wiki/module/` 页。
- 跑 `seed wiki index --write` 刷新索引和日志。

建议用户先跑 `/seed-kit:review-prd`（独立审查 PRD + 读代码对账），再进 impl。由用户决定是否触发 review-prd，不自动进入 impl。
