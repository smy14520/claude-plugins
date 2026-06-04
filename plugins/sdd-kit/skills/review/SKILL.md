---
name: review
description: "Audit one sdd-kit package PRD scope after impl. Reads PRD + impl evidence + diff, then records APPROVED / APPROVED_WITH_NOTES / NEEDS_REWORK / BRAINSTORM_DRIFT through sdd-arbor. Does not edit code or requirements."
---
# Review — semantic audit
使用语言：中文。
Review 检查 impl 的 DONE 声明是否真正满足 package PRD。它不是普通 code review、PR approval、自动修复器或自动修复面板。
## 输入
- package；裸 slice 名称不可视为执行单元。
- 必读：`prd.md`、`task.json`、`required_checks`、`checks`、impl evidence、actual `git diff`。
- 可读：PRD 引用 artifacts、`context/review.jsonl`、相关 `.wiki` 页面；wiki 只作 orientation。
## 数据字段使用
以下字段必须用于对账，不能只读自然语言：
| 字段 | 用途 |
|---|---|
| `required_checks` / `checks` / `impl_result.checks` / `impl_result.check_coverage` | 对账 required_check 是否有本次交付引用的 passed evidence；automated 承重命令只认 `run-check`、`exit_code` 和输出文件，`commands` 只是 legacy note |
| `acceptance` / `acceptance_coverage[S-NNN]` | 对照 PRD 每个 slice 完成标志，逐条找代码位置、测试位置或 check evidence；不能只回引 acceptance 文本本身 |
| `concerns` / `phase_history` | 计算 review 追加妥协与 impl 自报差距，并确认 impl 跑了几次 / 是否被退回过 |
## Audit 流程
1. **拆 PRD 完成标志** — 把 PRD `## Slices` 每个 slice 的 acceptance、边界、承重命令拆成原子条目。
2. **Required checks 对账** — 逐个确认 `impl_result.checks` / `check_coverage`，automated 必须有 `run-check` + `exit_code=0` + 可读输出，manual/blocked/not_run 必须有具体 reason/evidence；必要时可复跑且不能吞失败。
3. **三问对账** — 每条原子完成标志都问：实现存在？验证存在？验证够？negative-path / 业务层验证缺失都算缺口。
4. **数 concerns 差距** — 对比你 audit 出的妥协清单与 `impl_result.concerns` 长度差。
5. **填对账表 + 选 verdict** — 见报告模板与决策树；常见反模式参考 [`references/anti-patterns.md`](references/anti-patterns.md)。
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
- `NEEDS_REWORK` 回 impl；`BRAINSTORM_DRIFT` 回 brainstorm；APPROVED 不能只是「LGTM」。
- APPROVED / APPROVED_WITH_NOTES 后，提醒用户是否需要用 wiki skill publish 模块摘要。
