---
description: 跑 seed-kit review-loop：审代码+产物+prove-kill(批量证伪)+客观锚，loop 到收敛或熔断。自动定 task/slice，不用 install。
---

跑 seed-kit review-loop 审当前任务的实现。

**默认审整个 task（不带 slice 参数）**：impl 完成所有 slice 后跑**一次整体** review-loop（看全 diff + 全产物，直接修直到全绿），**不再每 slice 单独跑**。**Stop hook（`review_on_complete.py`）在 task 完成（所有 slice done）时查整体 review-loop marker**——整体 review-loop 跑完必须 `seed review-mark <task> --verdict <terminal_reason>` 落 task 级 marker，否则 Stop hook 拦 turn 收尾、反馈"先跑整体 review-loop"。带 slice 参数仅用于单独深审某 slice（可选）。

**步骤**：
1. 定 task/slice：task 从当前项目 `.arbor/tasks/` 推断（唯一目录直接用，多个问用户）；slice 从 `$ARGUMENTS` 取形如 `S-NNN` 的部分（**忽略 task 名前缀**——如 `todo S-001` 只取 `S-001`），省略则审整个任务。
2. 读 seed-kit 插件的 `templates/review-loop.template.js`。定位插件根用**确定性兜底**（`CLAUDE_PLUGIN_ROOT` 在 bash 子 shell 常为空）：`PLUGIN_ROOT=${CLAUDE_PLUGIN_ROOT:-$(dirname $(dirname $(readlink -f $(command -v seed))))}`，模板在 `$PLUGIN_ROOT/templates/review-loop.template.js`。
3. 用 **Workflow 工具**启动 review-loop：`script` = 该 template 内容，`args` = `{task, slice, repo: 当前项目根, jury?}`（`jury` 默认 1：1 个 validator 批量证伪全部 finding；设 2 加对抗冗余）。
4. **取 Workflow 返回值（关键，别用错 id）**：Workflow 是**异步**的——它立即返回一行 `Task ID: <短id>`（形如 `w2zukd2kn`）；transcript 路径里另有个更长的 `wf_...` **run-id，不要用它**。**只用那个短 Task ID**，调 `TaskOutput(task_id=<短id>, block=true, timeout=600000)` **阻塞等 Workflow 跑完**（review-loop 是多 agent 多轮，分钟级，timeout 给足、别中途放弃当前回合）。返回形如 `{result: {terminal_reason, converged, verdict, trace}}`——读 `result.terminal_reason`。Workflow 脚本本身**不能写文件**，所以必须靠 TaskOutput 把终态取回来。
5. 收敛判定由显式终态 `terminal_reason` 驱动：`converged`（客观锚全绿 + 两路 reviewer 非 null + 无 survived blocking）才可推进 done；`assert-stalled`（客观锚连续未绿）/ `assert-unavailable` / `reviewer-blind`（reviewer 返回 null）/ `circuit-breaker` / `rounds-exhausted` 都 escalate 交人，**绝不推 done**。注意：`converged` 代表客观 gate 过 + 无未决 blocking——不代表 reviewer 检出/排除过所有真实风险；minor/ok 级 finding 可能 survive（属质量债，不阻断 done）。
6. **落 task 级 marker（必须）**：拿到 `terminal_reason` 后跑 `seed review-mark <task> --verdict <terminal_reason> [--round N]`，终态写进 `.arbor/tasks/<task>/review-loop.json`。`review_on_complete` Stop hook 在所有 slice done 时查这个 marker——只有落了才放行 turn 收尾。

review-loop 会派 `seed-review`（审代码）/ `seed-judge`（审产物）/ `seed-validator`（批量证伪）/ `seed-assert`（客观锚：跑测试+质量命令）/ `seed-impl`（修）循环到收敛或熔断。

**结论在哪**：review-loop 的结论在 **`TaskOutput` 返回值的 `result`** 里（`terminal_reason` / `converged` / `verdict` / `trace`）。因为 Workflow 脚本不能写文件，必须 TaskOutput 取回 `terminal_reason`，再用 `seed review-mark` 落 task 级 `review-loop.json` marker（步骤 6，Stop hook 查它）。**不落 `review.md`**——逐验收条目对账由 `/seed-kit:review` 单独写 `review.md`（人读 + living-prd 展示）。

用法：`/seed-kit:review-loop S-001`（审 S-001）或 `/seed-kit:review-loop`（审整个 task）。
