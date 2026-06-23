---
description: 跑 seed-kit review-loop：审代码+产物+propose-kill(批量证伪)+客观锚，loop 到收敛或熔断。自动定 task/slice，不用 install。
---

跑 seed-kit review-loop 审当前任务（如 family-ledger）的实现。

**步骤**：
1. 定 task/slice：task 从当前项目 `.arbor/tasks/` 推断（唯一目录直接用，多个问用户）；slice 用 `$ARGUMENTS`（如 `S-005`），省略则审整个任务。
2. 读 seed-kit 插件的 `templates/review-loop.template.js`（用 `CLAUDE_PLUGIN_ROOT` 定位插件根）。
3. 用 **Workflow 工具**跑：`script` = 该 template 内容，`args` = `{task, slice, repo: 当前项目根, jury?}`（`jury` 默认 1：1 个 validator 批量证伪全部 finding；设 2 加对抗冗余）。
4. 收敛判定由显式终态 `terminal_reason` 驱动：`converged`（assert 全绿 + 两路 reviewer 非 null + 无 survived blocking）才可推进 done；`assert-stalled`（客观锚连续未绿）/ `assert-unavailable` / `reviewer-blind`（reviewer 返回 null）/ `circuit-breaker` / `rounds-exhausted` 都 escalate 交人，**绝不推 done**。
5. **落 marker（必须）**：Workflow 返回后跑 `seed review-mark <task> --slice <slice> --verdict <terminal_reason> [--round N]`，终态写进 `evidence/<slice>/review-loop.json`。`seed done` 的 review_gate hook 查这个 marker——只有 `converged` 放行勾选；缺 marker / 非 converged 会被拦并给出可执行下一步。

review-loop 会派 `seed-review`（审代码）/ `seed-judge`（审产物）/ `seed-validator`（批量证伪）/ `seed-assert`（客观锚）/ `seed-impl`（修）循环到收敛或熔断。

**结论在哪**：review-loop 的结论（`converged` / `escalated` / `verdict` / `trace`）在 Workflow 工具的返回值里。终态用 `seed review-mark` 落 `evidence/<slice>/review-loop.json`（done gate 查它，见步骤 5）。**不落 `review.md`**——逐条 AC 对账由 `/seed-kit:review` 单独写 `review.md`（人读 + living-prd 展示）；两者各管各的：marker 是"review-loop 跑过且收敛"的机器信号，review.md 是 AC 对账清单。

用法：`/seed-kit:review-loop S-005`（审 S-005）或 `/seed-kit:review-loop`（审整个 task）。
