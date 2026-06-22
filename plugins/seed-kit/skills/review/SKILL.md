---
name: review
description: "review 的入口。用户 /review → 选编排强度 → 调 review-loop（templates/review-loop.template.js + Workflow 工具）→ 它派 seed-review/seed-judge/seed-validator/seed-assert/seed-impl agent 做多轮 loop。review 本身是「审一次」的窄职责；loop/收敛/circuit breaker 在编排层，不在本 skill。"
---
# Review — 入口与编排

通用约定见 [`../references/conventions.md`](../references/conventions.md)。

review = 用**独立 agent** 审【代码】(seed-review) + 【产物】(seed-judge)，经 propose-kill (seed-validator) 证伪、assert (seed-assert) 客观锚，收敛由编排层判。**生成者 ≠ 验证者**：不依赖 impl 的叙述，只看 PRD + diff + evidence + 真实产物。

哲学：**gate 守对错（assert 客观），loop 守好坏（代码/产物质量）**。judge 进 loop（迭代体验），不做 gate 分数。详见 `CLAUDE.md`「验证哲学」。

## 何时 review

1. **软提醒**：`seed done` 后 PostToolUse hook 注入"建议 review"。
2. **用户触发**：`/review` 或"review 这个 slice"。
3. **impl 兜底**：impl 完成后建议触发。

## 怎么跑（编排不在本 skill）

loop/收敛/circuit breaker 全在编排层，不在 SKILL：

- **默认（中档）**：读 `templates/review-loop.template.js`，按 task/slice 填 args，用 Workflow 工具跑。模板用 JS 持 loop/收敛/circuit breaker（确定性，不靠 prompt 提醒）。收敛 = assert 全绿 + 无 survived blocking + circuit breaker 兜底（issues_hash 重复熔断）。
- **编排强度三档**（都在编排层）：轻 = subagent 单审；**中 = review-loop workflow（默认）**；重 = agent team 对抗（opt-in，环境支持时）。

## 对账标准（review 的判断依据，详细执行在 agents/seed-review.md）

- 先读项目的 `CLAUDE.md`、`.claude/rules/`、`DESIGN.md`——硬规则与审美标准；项目无则用通用地板。
- 逐条 AC 映射到代码/证据，含失败路径。
- 专查偷懒签名、验证降级、交付面冒充、过期声明、覆盖缺口、措辞红旗——这些是 seed-review 的职责方向。
- 感知型判断（切片是否纵向完整、scope 是否割裂）gate 不了，靠语义审。

## 角色（agent 定义在 `agents/`，各窄职责、角色硬分离）

| agent | 审什么 | 产出 |
|---|---|---|
| seed-review | 代码 diff/source | finding（只读，禁改码） |
| seed-judge | 真实产物（截图/运行页） | 体验 finding（按 rubric） |
| seed-validator | 证伪每条 finding | verdict valid/invalid |
| seed-assert | 跑 run-check | 客观 pass/fail + evidence |
| seed-impl | 按 finding 改码 | 改动摘要（守 PASS_TO_PASS） |

review 审一次、出 finding 即停；多轮 loop 由编排层驱动。

## 输出

结论**追加**到 `.arbor/tasks/<task>/review.md`（不覆盖历史）：每轮 `## Round N` + finding + validator verdict + 收敛/熔断状态。objective evidence 由 seed-assert 落 `evidence/`。

## 边界

不改代码（seed-impl 才改）、不改 prd、不动 checkbox。收敛判据在编排层。熔断或需返工时列清单交人，不自动触发下一轮。
