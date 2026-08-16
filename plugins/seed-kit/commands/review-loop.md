---
description: 跑 seed-kit review-loop：审代码+产物+prove-kill(批量证伪)+客观锚，loop 到收敛或熔断。自动定 task/slice，不用 install。
---

跑 seed-kit review-loop 审当前任务的实现。

**默认审整个 task（不带 slice 参数）**：impl 完成所有 slice 后跑**一次整体** review-loop（看全 diff + 全产物，直接修直到全绿）。整体 review-loop 跑完必须 `seed review-mark <task> --verdict <terminal_reason>` 落 task 级 marker，保存本次明确终态。带 slice 参数仅用于单独深审某 slice（可选）。

**步骤**：
1. 定 task/slice：task 从当前项目 `.arbor/tasks/` 推断（唯一目录直接用，多个问用户）；slice 从 `$ARGUMENTS` 取形如 `S-NNN` 的部分（**忽略 task 名前缀**——如 `todo S-001` 只取 `S-001`），省略则审整个任务。**审整个任务前先跑 `seed status <task>`**：存在未完成 slice 时不启动循环——先逐个 `seed done` 关闭，或该 slice 无法用命令验证时修 PRD（并入可验证条目或移入 Goal/Out of Scope）。未完成 task 的 converged marker 会被 `seed review-mark` 直接拒绝。
2. 定位模板绝对路径（**只定位，不读内容**）。定位插件根用**确定性兜底**（`CLAUDE_PLUGIN_ROOT` 在 bash 子 shell 常为空）：`PLUGIN_ROOT=${CLAUDE_PLUGIN_ROOT:-$(dirname $(dirname $(readlink -f $(command -v seed))))}`，模板在 `$PLUGIN_ROOT/templates/review-loop.template.js`——用 `echo` 打印这个绝对路径备用。
3. 用 **Workflow 工具**启动 review-loop：传 `scriptPath` = 上一步打印的模板绝对路径和 `args` = `{task, slice?, jury?}`，**不要同时传 `name`**（`name` 会被当作已保存 workflow 解析）。**不要把模板内容抄进 `script` 参数**——转录会引入丢行/注释化事故（有实录：整个脚本体被注释化后空转返回 success）；`scriptPath` 由 runtime 从磁盘读原文。template 固定以 Workflow 启动时的 cwd（`.`）为项目根，不猜测或拼接 `HOME/workdir`。`jury` 默认 1：1 个 validator 批量证伪全部 finding；设 2 加对抗冗余。
4. **等待协议（关键，循环 re-block 直到终态）**：Workflow 是**异步**的——它立即返回一行 `Task ID: <短id>`（形如 `w2zukd2kn`）；transcript 路径里另有个更长的 `wf_...` **run-id，不要用它**。**只用那个短 Task ID**，调 `TaskOutput(task_id=<短id>, block=true, timeout=600000)` 阻塞等待。review-loop 是多 agent 多轮，分钟级，**单次 600000ms 超时后循环仍可能在跑**：若返回 `retrieval_status=timeout` 或 `status=running`，**立刻用同一 task_id 再次调用 TaskOutput，如此循环直到拿到 result 为止**。等待期间不做任何其他动作——不翻目录、不自己跑测试、更不得在拿到终态前 `seed review-mark`。返回形如 `{result: {terminal_reason, converged, verdict, trace}}`——读 `result.terminal_reason`。Workflow 脚本本身**不能写文件**，所以必须靠 TaskOutput 把终态取回来。
5. 收敛判定由显式终态 `terminal_reason` 驱动：`converged`（客观锚全绿 + 两路 reviewer 非 null + 无 survived blocking）才可推进 done；`assert-stalled`（客观锚连续未绿）/ `assert-unavailable` / `reviewer-blind`（reviewer 返回 null）/ `circuit-breaker` / `rounds-exhausted` 都 escalate 交人，**绝不推 done**。注意：`converged` 代表客观 gate 过 + 无未决 blocking——不代表 reviewer 检出/排除过所有真实风险；minor/ok 级 finding 可能 survive（属质量债，不阻断 done）。
6. **落 task 级 marker（必须）**：拿到 `terminal_reason` 后跑 `seed review-mark <task> --verdict <terminal_reason> --depth full [--round N]`，终态写进 `.arbor/tasks/<task>/review-loop.json`，作为这次 review-loop 的 durable result。

review-loop 会派 `seed-review`（审代码）/ `seed-judge`（审产物）/ `seed-validator`（批量证伪）/ `seed-assert`（客观锚：跑测试+质量命令）/ `seed-impl`（修）循环到收敛或熔断。

**结论在哪**：review-loop 的结论在 **`TaskOutput` 返回值的 `result`** 里（`terminal_reason` / `converged` / `verdict` / `trace`），取回 `terminal_reason` 后用 `seed review-mark` 落 task 级 marker（步骤 6）。**不落 `review.md`**——逐验收条目对账由 `/seed-kit:review` 单独写 `review.md`（人读 + living-prd 展示）。

用法：`/seed-kit:review-loop S-001`（审 S-001）或 `/seed-kit:review-loop`（审整个 task）。
