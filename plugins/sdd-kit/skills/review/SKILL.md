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
- 必读：`prd.md`、`task.json`、`required_checks`、`checks`、impl evidence、actual `git diff`。
- 如 PRD 引用 `.arbor/tasks/<package>/artifacts/` 中的 data-model / integration / API contract，必须读取并纳入审计。
- 可读：`context/review.jsonl`、相关 `.wiki` 页面；wiki 只作 orientation。

## 数据字段使用

impl 已经把审计材料结构化到 `task.json`，review 必须用这些字段对账，不能只读自然语言：

| 字段 | 用途 |
|---|---|
| `required_checks` | slice Verification 派生出的应验证清单；review 逐项审是否被满足 |
| `checks` | `run-check` / `record-check` 产生的 evidence；读取 `stdout_path` / `stderr_path` / `exit_code` / `evidence` |
| `impl_result.checks` | impl 声称支撑结果的 check id 列表；不在这里的 check 不算本次交付证据 |
| `impl_result.check_coverage` | required_check 到 check id 的覆盖关系；缺失或 incomplete = 缺口 |
| `acceptance` | 对照 PRD 每个 slice 完成标志，逐条找代码 / 测试证据 |
| `concerns` | 与你 audit 出的妥协清单数差；差 ≥3 → NEEDS_REWORK |
| `acceptance_coverage[S-NNN]` | 每个 slice 至少 1 条独立证据（代码位置 / 测试位置 / check evidence）；不能只回引 acceptance 文本本身 |
| `phase_history` | 找 impl 跑了几次 / 是否被 review 退回过 |

`commands` 是 legacy note，不是 verification evidence。承重命令是否真的跑过，只认 `checks` 里的 `source=run-check`、`command`、`exit_code` 和输出文件。

## Audit 流程

逐 slice 机械对账，不要扫一眼就 APPROVED：

1. **拆 PRD 完成标志** — 把 PRD `## Slices` 每个 slice 的 acceptance、边界、承重命令拆成原子条目。
2. **Required checks 对账** — 对每个 `required_check`：
   - 找 `impl_result.checks` 中引用的对应 check id；找不到 → 缺口。
   - automated kind / 有 command_hint 的 check 必须有 `source=run-check`、`exit_code=0` 和可读的 `stdout_path` / `stderr_path`；不接受 impl 自然语言声称。
   - manual check 必须有具体 `evidence`；blocked/not_run 必须有 reason + evidence，并按 verdict 规则处理。
   - 需要确认时可独立复跑 `sdd-arbor run-check <package> --required-check <req_id> -- <command>`，但不要把复跑失败吞掉。
3. **三问对账** — 对每条原子完成标志：
   - **a. 实现存在？** 在 diff / 代码里找；找不到 → 缺口。
   - **b. 验证存在？** 找对应 check evidence 或测试断言；找不到 → 缺口。
   - **c. 验证够？** PRD 写「X 被阻止 / 拒绝 / 限制」必须有 negative-path 断言或对应 check；数据库 unique / NOT NULL 约束不算业务层验证。
4. **数 concerns 差距** — 你 audit 出的妥协清单 vs `impl_result.concerns` 长度差。
5. **填对账表 + 选 verdict** — 见报告模板与决策树。

反模式见 [`references/anti-patterns.md`](references/anti-patterns.md)，它列举了真实会出现的 impl 产出盲区（mega-test / dead file / 承重命令未跑 / negative-path 缺测等），review 必须主动找。

## Verdict 决策树

按顺序，首条命中即判定：

1. PRD 本身错误 / 失效 / 与现有 repo 脱节 → **BRAINSTORM_DRIFT**
2. 任一 required_check 没有 passed evidence，且 impl_result 是 DONE → **NEEDS_REWORK**
3. 任一 automated required_check 只有 manual/record-check 声明，没有 `run-check` exit_code=0 → **NEEDS_REWORK**
4. 任一 slice 完成标志在 diff 中找不到对应实现 → **NEEDS_REWORK**
5. 任一 slice 完成标志没有对应测试断言或 check evidence（且非纯展示） → **NEEDS_REWORK**
6. 你 audit 出 impl 漏掉的 concerns ≥3 条 → **NEEDS_REWORK**
7. 漏 concerns 1-2 条且无其它缺口 → **APPROVED_WITH_NOTES**（note 里追加遗漏 concern）
8. 全部对账通过且 0 漏 → **APPROVED**

四态含义：

| 状态 | 含义 |
|------|------|
| APPROVED | 当前 diff 满足 PRD scope 与验收，无遗漏 concern |
| APPROVED_WITH_NOTES | 语义正确，有轻微 concern 遗漏或后续建议 |
| NEEDS_REWORK | diff 与 PRD / impl evidence 存在语义差距 |
| BRAINSTORM_DRIFT | PRD 本身错误、失效或与当前 repo 脱节 |

Package review 通过不等于 merged / delivered；它只说明当前 package PRD scope 已通过语义审计。

## 报告模板

````md
结论：<verdict>。<一句话总结>

### 完成标志对账

| Slice | 完成标志（从 PRD 拷） | 实现位置 | 测试 / check evidence | 缺口 |
|---|---|---|---|---|
| S-001 | <PRD 原文> | `<file>:<line>` | `chk_001` / `<test file>:<line>` | 无 / <具体缺口> |

### Required checks 对账

| Required check | Kind | Evidence | 结果 | 缺口 |
|---|---|---|---|---|
| `req_S001_001` | test | `chk_001` stdout_path=`checks/chk_001.stdout` | passed | 无 / <具体缺口> |

### Concerns 对账

| 类型 | impl 自报 | review 追加 |
|---|---|---|
| Mock / Fake 替代真实持久化 | 0 | <数量+证据> |
| required_check 缺 evidence | 0 | <数量+req id> |
| 承重命令未跑 | 0 | <数量+具体 command_hint> |
| Negative-path 缺测 | 0 | <数量+具体边界> |
| Mega-test 假装多断言 | 0 | <数量+test 文件> |
| Dead file（写了没接） | 0 | <数量+文件路径> |

### 通过检查

- <具体确认通过的关键点>

### 下一步

- <按 verdict 的 follow-up 指引>
````

## 输出

- 使用 `sdd-arbor record-review <package> --state <verdict> --summary "..." --evidence "..." --note "..."` 更新 lifecycle 并追加 review log。
- 若 verdict 是 `NEEDS_REWORK`，下一步回 impl，按对账表「缺口」列修复。
- 若 verdict 是 `BRAINSTORM_DRIFT`，建议回 brainstorm 追加 amendment；不要让 impl 背锅。
- APPROVED 不能只是「LGTM」；至少在对账表里给出每个 slice 的实现 + 测试位置。
- APPROVED 或 APPROVED_WITH_NOTES 后，提醒用户是否需要用 wiki skill publish 模块摘要，以便后续开发时快速定位该模块的契约、关键决策和跨模块关系。
