---
name: brainstorm
description: "把模糊需求收敛成一个 package PRD。持续更新 .arbor/tasks/<package>/prd.md 草稿（含 Technical Framing 与 ordered Slices），通过 sdd-arbor finalize-brainstorm 写入 ready package。"
---

# Brainstorm — PRD-first package

通用约定见 `../references/conventions.md`。

Brainstorm 的唯一产物是 `.arbor/tasks/<package>/prd.md`：创建或定位 draft → 每轮用户回答后更新 PRD → 扩展扫视与定稿自检通过 → `sdd-arbor finalize-brainstorm` 写入 ready package。

## Hard rules

1. 每轮回答后先更新 PRD 草稿，再问下一个问题。
2. 离散取舍必须用 `AskUserQuestion` 给 2-4 个选项；推荐项放第一，推荐项 description 中说明推荐理由。选项描述用技术后果区分（"X 会导致 Y"），不要用 scope 大小或"初版/MVP/后续"来暗示哪个该选——范围决策是用户的事，不是选项描述的事。
3. 不手写 `.arbor` control state；ready package 只通过 `sdd-arbor finalize-brainstorm` 写入。
4. 未得到用户对最终摘要的**明确确认**前，不调用 `sdd-arbor finalize-brainstorm`。
5. `## Slices` 是 brainstorm 的产物，PRD 内只写 slice 需求与顺序，不维护第二套执行计划。
6. 一次只问一个最高价值问题；能读代码回答的不要问用户。

## Setup

用户指定 package name 时优先使用；否则用 `MM-DD-<topic-slug>`，同日同主题加更具体后缀，不覆盖旧 package。
新需求用 `sdd-arbor create <package>` 创建；续作时按用户给定名称读取 draft，自然语言续作则扫描 `.arbor/tasks/*/prd.md`，多候选只问一次确认。
模式选择遵从用户明说；需求已含目标/范围/场景/验收/非目标/技术边界时默认 normal；其它情况 ask，推荐 grill-me。模式节奏见 `references/interview-modes.md`。

## Loop

每次被唤醒：若用户回答了上个问题，先更新 PRD；再读 PRD 当前状态，必要时读取新增相关代码区域。
沿用户场景逐个展开触发、行为、成功判定、退化路径和交叉影响，直到行为级精度。
仍缺关键决策时按 Hard rule 2 问一个最高价值问题并停下等用户；全部收敛后进入 Finalize。
质量锚：一个从未见过这个项目的工程师，只读 PRD 就能实现全部场景，不需要回来问任何行为决策。

## Reference pointers

项目画像推断与已有信息注入策略见 `references/context-first.md`。
Technical Framing 通用项、画像特定项与档位见 `references/technical-framing.md`。
非平凡 schema / 协议 / 状态机 / 权限矩阵的 artifact 用法见 `references/artifacts.md`。
Wiki 引用触发条件、三层结构与 fallback 见 `../wiki/references/page-types.md`。
PRD 必须包含 `## Slices`，按行为级 checkpoint 切分。切分原则和反模式见 `references/slices.md`。
Slice Tasks 在 finalize 前写入 `.arbor/tasks/<package>/slices/S-NNN.md`；模板和必需段落见 `assets/templates/slice-task.md`。

## Finalize

定稿前按 `references/finalize-criteria.md` 自检；不通过就继续编辑，不向用户确认。
自检通过后给用户最终摘要并请求明确确认；确认前不得调用 `finalize-brainstorm`。
确认后执行 `sdd-arbor finalize-brainstorm --input-json '{"name":"<package>","kind":"single","prd_path":".arbor/tasks/<package>/prd.md"}'`。
停在 impl 前，告诉用户下一步用 impl。

## Amendment 入口

review 判定 BRAINSTORM_DRIFT 后回 brainstorm 时走 amendment 流程，只针对 drift 追问，不重开完整循环。详见 `references/amendments.md`。

## Scope

- 不采集 raw evidence（用 research）。
- 不写代码（用 impl）。
- 不做语义审计（用 review）。
