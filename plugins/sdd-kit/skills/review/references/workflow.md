# Review workflow 边界细节

主文件 `SKILL.md` 已经定义了 Audit 流程、Verdict 决策树和报告模板。本文件只保留执行时容易漏的边界细节。

## Slice 标记不是事实，代码 diff 才是

`task.json.slices[].status=done` 只是 impl 的声明；review 必须用 `git diff` 验证对应代码确实落地。`acceptance_coverage` 字段也是声明，要逐条对照实际文件位置。

## Legacy PRD fallback

若缺 `.arbor/tasks/<package>/prd.md`，legacy `.arbor/brainstorms/<name>.md` 只能作为 fallback，并在 review 报告里标为「迁移风险」，建议 brainstorm 把内容迁回 `prd.md`。

## Wiki 仅作 orientation

`.wiki` 页面 / `sdd-arbor wiki-collect` 帮助 review 快速理解模块上下文，但不能用 wiki 推翻 PRD。PRD 是当前 package scope 的事实源。

## PRD 描述不足但方向清楚

不属于 BRAINSTORM_DRIFT（drift 要求 PRD 真错或失效）。该走的路：让用户回 brainstorm 把 PRD 补到可执行，再让 impl 重跑。Review 不引入第二套执行计划。

## 多 slice 累积 diff 隔离

当前 package 的 diff 可能与历史 diff 混杂。报告里必须说明本次审计对应哪些 diff files / 哪些 slice，避免把别的 package 的问题计到本次。
