---
name: brainstorm
description: "把模糊需求收敛成一个 package PRD。持续更新 .arbor/tasks/<package>/prd.md 草稿（含 Technical Framing 与 ordered Slices），通过 sdd-arbor finalize-brainstorm 写入 ready package。"
---

# Brainstorm — PRD-first package

通用约定见 [`../references/conventions.md`](../references/conventions.md)。

Brainstorm 的唯一产物是 `.arbor/tasks/<package>/prd.md`：创建或定位 draft → 每轮用户回答后更新 PRD → 扩展扫视与定稿自检通过 → `sdd-arbor finalize-brainstorm` 写入 ready package。

## Hard rules

1. 每轮回答后先更新 PRD 草稿，再问下一个问题。
2. 离散取舍必须用 `AskUserQuestion` 给 2-4 个选项；推荐项放第一，推荐项 description 中说明推荐理由。
3. 不手写 `.arbor` control state；ready package 只通过 `sdd-arbor finalize-brainstorm` 写入。
4. 未得到用户对最终摘要的**明确确认**前，不调用 `sdd-arbor finalize-brainstorm`。
5. `## Slices` 是 brainstorm 的产物，PRD 内只写 slice 需求与顺序，不维护第二套执行计划。
6. 一次只问一个最高价值问题；能读代码回答的不要问用户。

## Setup

**Package name.** 用户指定时优先使用；否则 `MM-DD-<topic-slug>`（kebab-case，避免中文/空格）。例："知识付费系统" → `05-02-knowledge-paid-system`。同日同主题已存在时加更具体后缀，不覆盖旧 package。

**定位 draft.** 新需求用 `sdd-arbor create <package>` 创建。续作时用户给名字就直接读 `.arbor/tasks/<package>/prd.md`；自然语言续作（用户只说 topic / "继续某需求"）扫描 `.arbor/tasks/*/prd.md`，多候选时只问一次确认。

**模式选择.**

| 信号 | 动作 |
|---|---|
| 用户明说 `normal` / `grill-me` / 直接定稿 | 遵从 |
| 需求已含目标/范围/场景/验收/非目标/技术边界 | 默认 normal |
| 其它（含刚从 research 进来，research 是上下文，不是需求冻结） | ask，推荐 grill-me |

Ask 时 option 固定给 `normal` 与 `grill-me`，description 里写当前上下文下为什么推荐。模式节奏见 [`references/normal.md`](references/normal.md) / [`references/grill-me.md`](references/grill-me.md)。

## Loop

每次被唤醒按序执行：

1. **先落盘**：如果用户本轮回答了上一个问题，立即更新 PRD（`Open Questions` 调整；`Requirements (evolving)` / `Acceptance Criteria (evolving)` / `Technical Framing` 追加；`Interview Log` 只记关键问答和需求变化，不记聊天流水）。
2. 读 PRD 当前状态 / 相关代码 / 已有 research 做上下文。
3. 一句话说明当前理解与**真正阻塞 finalize** 的缺口。
4. 有缺口 → 按 Hard rule 2 用 `AskUserQuestion` 问一个最高价值问题，**停下等用户**；没有 → 进入 Finalize。

## 已有信息注入

来源不论是现有代码、research 材料、还是用户自带规格（SQL / API 文档 / 参考设计），都先写进 `What I already know` 和 `Technical Framing`：

- **存量项目**：第一轮追问前主动读相关代码，把变更方案（改哪些表/模块、新建什么、接入点、不能动的边界）写入 PRD。
- **Research 材料**：显式区分 research 已支持的事实、候选方向、未由用户确认的假设。定位 topic 时只读 `.arbor/research/*/index.md` 的 title 和摘要，不遍历全部 research；多候选 `AskUserQuestion` 让用户确认。
- **用户自带规格**：SQL/API/接口契约原样写入 PRD 对应 section 作为基准约束，**不再**通过 grill-me 重新推导；发现技术问题（缺索引、类型不当、与现有结构冲突）时用 `AskUserQuestion` 提具体建议。规格与代码分析冲突时 `AskUserQuestion` 确认以哪个为准。

## Technical Framing

PRD 必须收敛承重技术边界，避免 impl 在关键架构问题上自由发挥。覆盖 stack / auth / module 边界 / data / admin / integration / testing / migration 档位。Testing strategy 档位用 `AskUserQuestion` 让用户选。详见 [`references/technical-framing.md`](references/technical-framing.md)。

**非平凡 schema / 协议 / 状态机 / 权限矩阵** 用 package artifact 承载草案级 contract，详见 [`references/artifacts.md`](references/artifacts.md)。

## Wiki 引用

Technical Framing 触及跨模块同步修改、既有模块契约、历史决策、踩过的坑时，先：

```bash
sdd-arbor wiki-collect --query "<keyword>" --limit 5 --json
```

只引用 helper 实际返回的 page title/path。引用时保持三层结构（核心 scope 在 PRD 自包含 / wikilink 只做防漏 / 写 fallback），详见 [`../wiki/references/page-types.md`](../wiki/references/page-types.md)。纯算法 / 纯 utility / 纯 typo fix / 完全孤立的新增功能跳过。

## Slices

PRD 定稿必须包含 `## Slices`，按依赖顺序写出有序实现切片。Slices 是 brainstorm 的产物——此时细节最多、切片最精准。每个 slice 是**独立可验证的小单元**（契约 / 功能 / 行为 / 状态转换），不是某层动作的完成；第一个通常是 walking skeleton。详细切分原则、字段、反例、退化护栏见 [`references/slices.md`](references/slices.md)。

## Finalize

PRD 定稿前：

1. **扩展扫视** — 未来演进 / 相关场景 / 失败与边界 哪些纳入本次 package scope，哪些进 Out of scope。
2. **Open Questions 处理** — blocking 必须解决；non-blocking 移入 Out of scope / Risks / Assumptions 并写处理方式。
3. **PRD 收尾整理** — evolving 内容落入正式 section；删占位符；顶层 `Open Questions` 空或只留 non-blocking。
4. **自检** — 不通过继续编辑，不向用户确认。

详细条件见 [`references/finalize-criteria.md`](references/finalize-criteria.md)（PRD 定稿条件逐项）。

自检通过后给用户最终摘要并**请求确认**。**收到用户明确确认前不要调用 `finalize-brainstorm`**（Hard rule 4）。确认后：

```bash
sdd-arbor finalize-brainstorm --input-json '{"name":"<package>","kind":"single","prd_path":".arbor/tasks/<package>/prd.md"}'
```

停在 impl 前，告诉用户下一步用 impl。

## Amendment 入口

review 判定 BRAINSTORM_DRIFT 后回 brainstorm 时走 amendment 流程，只针对 drift 追问，不重开完整循环。详见 [`references/amendments.md`](references/amendments.md)。

## Scope

- 不采集 raw evidence（用 research）。
- 不写代码（用 impl）。
- 不做语义审计（用 review）。
