---
description: 跑 seed-kit review-loop：审代码+产物+propose-kill(批量证伪)+客观锚，loop 到收敛或熔断。自动定 task/slice，不用 install。
---

跑 seed-kit review-loop 审当前任务的实现。

**步骤**：
1. 定 task/slice：task 从当前项目 `.arbor/tasks/` 推断（唯一目录直接用，多个问用户）；slice 从 `$ARGUMENTS` 取形如 `S-NNN` 的部分（**忽略 task 名前缀**——如 `todo S-001` 只取 `S-001`），省略则审整个任务。
2. 读 seed-kit 插件的 `templates/review-loop.template.js`。定位插件根用**确定性兜底**（`CLAUDE_PLUGIN_ROOT` 在 bash 子 shell 常为空）：`PLUGIN_ROOT=${CLAUDE_PLUGIN_ROOT:-$(dirname $(dirname $(readlink -f $(command -v seed))))}`，模板在 `$PLUGIN_ROOT/templates/review-loop.template.js`。
3. 用 **Workflow 工具**启动 review-loop：`script` = 该 template 内容，`args` = `{task, slice, repo: 当前项目根, jury?}`（`jury` 默认 1：1 个 validator 批量证伪全部 finding；设 2 加对抗冗余）。
4. **取 Workflow 返回值（关键，别用错 id）**：Workflow 是**异步**的——它立即返回一行 `Task ID: <短id>`（形如 `w2zukd2kn`）；transcript 路径里另有个更长的 `wf_...` **run-id，不要用它**。**只用那个短 Task ID**，调 `TaskOutput(task_id=<短id>, block=true, timeout=600000)` **阻塞等 Workflow 跑完**（review-loop 是多 agent 多轮，分钟级，timeout 给足、别中途放弃当前回合）。返回形如 `{result: {terminal_reason, converged, verdict, trace}}`——读 `result.terminal_reason`。Workflow 脚本本身**不能写文件**，所以必须靠 TaskOutput 把终态取回来。
5. 收敛判定由显式终态 `terminal_reason` 驱动：`converged`（assert 全绿 + 两路 reviewer 非 null + 无 survived blocking）才可推进 done；`assert-stalled`（客观锚连续未绿）/ `assert-unavailable` / `reviewer-blind`（reviewer 返回 null）/ `circuit-breaker` / `rounds-exhausted` 都 escalate 交人，**绝不推 done**。注意：`converged` 仅代表"声明义务过了客观 gate + 无未决 blocking"——不代表 reviewer 检出/排除过所有真实风险；minor/ok 级 finding 可能 survive（属质量债，不阻断 done，这是设计、非漏审）。
6. **落 marker（必须）**：拿到 `terminal_reason` 后跑 `seed review-mark <task> --slice <slice> --verdict <terminal_reason> [--round N]`，终态写进 `evidence/<slice>/review-loop.json`。`seed done` 的 review_gate hook 查这个 marker——只有 `converged` 放行勾选；缺 marker / 非 converged 会被拦并给出可执行下一步。

review-loop 会派 `seed-review`（审代码）/ `seed-judge`（审产物）/ `seed-validator`（批量证伪）/ `seed-assert`（客观锚）/ `seed-impl`（修）循环到收敛或熔断。

**结论在哪**：review-loop 的结论在 **`TaskOutput` 返回值的 `result`** 里（`terminal_reason` / `converged` / `verdict` / `trace`）。因为 Workflow 脚本不能写文件，必须 TaskOutput 取回 `terminal_reason`，再用 `seed review-mark` 落 `evidence/<slice>/review-loop.json`（done gate 查它，见步骤 6）。**不落 `review.md`**——逐条 AC 对账由 `/seed-kit:review` 单独写 `review.md`（人读 + living-prd 展示）；两者各管各的：marker 是"review-loop 跑过且收敛"的机器信号，review.md 是 AC 对账清单。

用法：`/seed-kit:review-loop S-001`（审 S-001）或 `/seed-kit:review-loop`（审整个 task）。
