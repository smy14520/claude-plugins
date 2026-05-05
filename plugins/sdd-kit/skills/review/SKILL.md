---
name: review
description: "Audit one sdd-kit package PRD scope after impl. Reads PRD + impl evidence + diff, then records APPROVED / APPROVED_WITH_NOTES / NEEDS_REWORK / BRAINSTORM_DRIFT through sdd-arbor. Does not edit code or requirements."
---

# Review — semantic audit

使用语言：中文。

Arbor helper 入口、路径和常用命令见 [`../references/arbor-helper.md`](../references/arbor-helper.md)；运行前遵守其中约定。

Review 检查 impl 的 DONE 声明是否真正满足 package PRD。它不是普通 code review、PR approval、自动修复器或 Team Auto panel。

## Team Auto handoff

如果用户明确要求 Team Auto / 多 agent / review panel，先使用 `team-auto` 选择阵型；Team 完成后主会话再按本 skill 给最终 verdict。

## 输入

- package；裸 slice 名称不可视为执行单元。
- 必读：`prd.md`、`task.json`、impl evidence、actual `git diff`。
- 如 PRD 引用 `.arbor/tasks/<package>/artifacts/` 中的 data-model / integration / API contract，必须读取并纳入审计。
- 可读：`context/review.jsonl`、相关 `.wiki` 页面；wiki 只作 orientation。

## 审查重点

按当前 diff 选择重点，不机械逐项输出：

- PRD 目标、scope、关键场景是否被满足。
- Acceptance Criteria、Technical Framing、Package artifacts contract 与 `## Slices` 是否被满足。
- impl evidence 和 self-check 是否支撑 DONE。
- diff 是否 scope creep、遗漏关键路径或破坏 out of scope。
- PRD Testing strategy 是否被落地：选了核心路径测试或 TDD，impl 是否实际写了对应测试；选了最小验收，是否至少跑了 happy path。
- 测试、状态一致性、安全、权限、数据迁移、并发等承重语义是否可靠。
- 是否违反当前 repo 模式或项目规则。

## 四态 verdict

| 状态 | 含义 |
|------|------|
| APPROVED | 当前 diff 满足 PRD scope 与验收 |
| APPROVED_WITH_NOTES | 语义正确，但有轻微问题或后续建议 |
| NEEDS_REWORK | diff 与 PRD / impl evidence 存在语义差距 |
| BRAINSTORM_DRIFT | PRD 本身错误、失效或与当前 repo 脱节 |

Package review 通过不等于 merged / delivered；它只说明当前 package PRD scope 已通过语义审计。

## 输出

- 使用 `sdd-arbor record-review <package> --state <verdict> --summary "..." --evidence "..." --note "..."` 更新 lifecycle 并追加 review log。
- 若 verdict 是 `NEEDS_REWORK`，下一步回 impl 处理当前 package。
- 若 verdict 是 `BRAINSTORM_DRIFT`，建议回 brainstorm 追加 amendment；不要让 impl 背锅。
- APPROVED 不能只是 “LGTM”；至少说明检查了哪些 goal / scope / diff evidence。
- APPROVED 或 APPROVED_WITH_NOTES 后，提醒用户是否需要用 wiki skill publish 模块摘要，以便后续开发时快速定位该模块的契约、关键决策和跨模块关系。
