---
description: 跑 seed-kit review-loop：审代码+产物+propose-kill(3票)+客观锚，loop 到收敛或熔断。自动定 task/slice，不用 install。
---

跑 seed-kit review-loop 审当前任务（如 family-ledger）的实现。

**步骤**：
1. 定 task/slice：task 从当前项目 `.arbor/tasks/` 推断（唯一目录直接用，多个问用户）；slice 用 `$ARGUMENTS`（如 `S-005`），省略则审整个任务。
2. 读 seed-kit 插件的 `templates/review-loop.template.js`（用 `CLAUDE_PLUGIN_ROOT` 定位插件根）。
3. 用 **Workflow 工具**跑：`script` = 该 template 内容，`args` = `{task, slice, repo: 当前项目根}`。
4. 收敛判定由显式终态 `terminal_reason` 驱动：`converged`（assert 全绿 + 两路 reviewer 非 null + 无 survived blocking）才可推进 done；`assert-stalled`（客观锚连续未绿）/ `assert-unavailable` / `reviewer-blind`（reviewer 返回 null）/ `circuit-breaker` / `rounds-exhausted` 都 escalate 交人，**绝不推 done**。

review-loop 会派 `seed-review`（审代码）/ `seed-judge`（审产物）/ `seed-validator`（3 票证伪）/ `seed-assert`（客观锚）/ `seed-impl`（修）循环到收敛或熔断。

**结论在哪**：review-loop 的结论（`converged` / `escalated` / `verdict` / `trace`）在 Workflow 工具的返回值里，**不落 `review.md`**——逐条 AC 对账仍由 `/seed-kit:review` 写 `review.md`。若要跨 session 留痕，把返回值原样快照落 `.arbor/tasks/<task>/evidence/review-loop-<slice>.json`（**不要**写进 review.md：`review_trigger.py` 见到 `## Review` 标题会抑制重审提醒，loop 自写会焊死该 slice 的重审 gate）。

用法：`/seed-kit:review-loop S-005`（审 S-005）或 `/seed-kit:review-loop`（审整个 task）。
