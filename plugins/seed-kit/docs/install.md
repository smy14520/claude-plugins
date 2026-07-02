# review-loop 的用法

review SKILL 只管"审什么"（知识）。执行走三种模式之一，由用户指定或 Claude 按场景——**编排不在 review SKILL**。

## 模式 2（默认）：`/seed-kit:review-loop` command

最简单——**不用 install、不用重启**。在加载了 seed-kit 的项目里：

```
/seed-kit:review-loop
```

command 读 `templates/review-loop.template.js` + 用 Workflow 工具跑（审代码/产物 + propose-kill 批量证伪 + 客观锚，loop 到收敛或熔断）。

## 模式 1（轻）：subagent

Claude 自主用 Agent tool 派 `seed-kit:seed-review`。简单 slice / 快速查。直接对 Claude 说"用 seed-kit:seed-review 审 S-005"。

## 模式 3（重）：agent team

Claude 自主 TeamCreate 组 architect-A/B + devil's-advocate 对抗。高价值 / 架构争议。实验性。

## 默认（整体跑完一次 review-loop 即可）

impl 做完全部 slice → 跑一次整体 `/seed-kit:review-loop` 到 converged → `seed review-mark <task> --verdict converged` 落 marker。

收敛判定由 review-loop 的显式终态 `terminal_reason` 驱动：`converged` 才推 done；`assert-stalled` / `assert-unavailable` / `reviewer-blind` / `circuit-breaker` / `rounds-exhausted` 都 escalate 交人。

`review_on_complete` Stop hook 在所有 slice done 时检查 review-loop marker 是否存在——必须落了 marker 才放行 turn 收尾。

## 为什么不用 install

Claude Code 插件不分发 workflow（`workflows/` 非插件目录）。方向 2 用 command inline 调 Workflow，绕开 install + 重启——`/seed-kit:review-loop` 一句话直接跑。
