---
name: review
description: "仅当用户明确要求 sdd-kit package/T-xxx 语义审计时使用，例如 '用 review skill 审计 <package> 的 T-001'。对 impl DONE/DONE_WITH_CONCERNS 后的 actual diff 做只读审计：PRD + task + diff +（可选）wiki 是否一致。不要用于普通泛泛代码 review。输出 APPROVED / APPROVED_WITH_NOTES / NEEDS_REWORK / BRAINSTORM_DRIFT，并通过 sdd-arbor 追加 review log / 更新 task.json。"
---

# Review — Package semantic audit

使用语言：中文。

Review 是 sdd-kit 的 package/T-xxx 语义审计 gate：检查 impl 的 DONE 声明是否真正满足 package-local PRD + task，而不是只看 SelfCheck 或测试是否通过。

它不是普通 code review、PR approval、自动修复器或 Team Auto review panel。需要多 agent 多角度审查时，用户可显式使用 Team Auto；最终 sdd-kit verdict 仍由主会话按本 skill 收口。

## Team Auto handoff

如果用户在 review 请求里明确写了 `Team Auto` / `team auto` / `agent team` / `多 agent` / `review panel` / `开 team`，不要直接进入普通 review。

先按 `skills/team-auto/SKILL.md` 的方式处理：根据当前 review 目标和 diff 形态，给出本次定制的 2–4 个阵型选项，让用户选择；Team 完成后，主会话再按本 skill 的四态 verdict 收口。

这里不复制 Team Auto 的阵型、worker prompt 或 Team 创建流程；这些只维护在 `skills/team-auto/`。

## 输入与边界

- 审计对象必须是 package + package-local T-xxx；裸 `T-001` 不可视为全局唯一任务。
- 必读：`.arbor/tasks/<package>/prd.md`、`task.md`、`task.json`、actual `git diff`。
- 可读：`context/review.jsonl`、相关 `.wiki` 页面；wiki 只作 orientation，结论必须回到 PRD / task / diff 验证。
- 只读代码、PRD 和 task definition；不编辑实现，不改 `prd.md` / `task.md`。
- 只通过 helper 追加 review log / 更新 lifecycle；不手写 `task.json` 或 context JSONL。

## Review lenses

默认从这些视角审，但按当前 diff 选择重点，不机械逐项输出：

- **需求语义**：PRD 目标、scope、关键场景、out of scope 是否被满足或被破坏。
- **Task 对齐**：deliverable、acceptance、context、ready-check 是否被尊重。
- **Diff 边界**：是否 scope creep、遗漏关键路径、修改了不该改的内容；当前 verdict 覆盖哪些 diff scope。
- **测试与回归**：task acceptance 的 observable behavior、edge case、amendment regression 是否有证据；是否用 mock 掩盖内部核心逻辑，或缺少必要的 UI/browser / 外部边界验证。
- **架构与可维护性**：实现是否符合既有模式，是否引入不必要复杂度或脆弱耦合。
- **安全与状态一致性**：权限、数据、交易、并发、状态迁移、幂等等承重语义是否安全。
- **项目公约**：是否违反与本 diff 相关的 `CLAUDE.md` / `.claude/rules` / wiki gotcha。

## 四态 verdict

| 状态 | 含义 |
|------|------|
| **APPROVED** | 当前 T-xxx 对应 diff 覆盖 PRD slice 与 task 范围，无保留意见 |
| **APPROVED_WITH_NOTES** | 语义正确，但有轻微问题或后续建议 |
| **NEEDS_REWORK** | diff 与 PRD / task 存在语义差距，impl 需重新处理 |
| **BRAINSTORM_DRIFT** | diff 看似合理，但 PRD 本身错误、失效或与当前 repo 脱节；回 brainstorm 做 forward-only amendment |

单个 T-xxx verdict 不等于 package PR approval；package readiness 由所有 required T-xxx 的 review 状态聚合。

## 输出

- 追加到 `.arbor/tasks/<package>/review.md`，审计正文默认中文；状态枚举、T-xxx、路径、命令、schema 字段和代码标识符保持原文。
- 使用 `sdd-arbor` 更新 `task.json` 中对应 T-xxx 的 review state、updated_at、顶层聚合状态和 phase history。
- 若有新的 review context，使用 `sdd-arbor add-context` / `add-context-batch --type review`。
- 若 verdict 是 `BRAINSTORM_DRIFT`，建议回 brainstorm 追加 `AMD-xxx`；不要让 impl 背锅。

推荐报告结构：

```md
结论：NEEDS_REWORK。<一句话说明>

问题清单：

1. 中等 — <问题>
   - 证据：<文件路径 / 命令 / diff 事实>
   - 影响：<为什么影响 package / T-xxx / 验收>
   - 建议处理：<下一步>

通过检查：

- <已确认通过的关键点>
```

APPROVED 不能只是 “LGTM”；至少说明 goal / scope / constraints / diff scope 已检查。
