# review 的三种模式

review SKILL 只管"审什么"（知识）。执行走三种模式之一，由用户指定或 Claude 按场景——**编排不在 review SKILL**。

## 模式 2（默认）：`/seed-kit:review-loop` command

最简单——**不用 install、不用重启**。在加载了 seed-kit 的项目里：

```
/seed-kit:review-loop S-005
```

command 读 `templates/review-loop.template.js` + 用 Workflow 工具跑（审代码/产物 + propose-kill 批量证伪 + 客观 assert 锚，loop 到收敛或熔断）。

## 模式 1（轻）：subagent

Claude 自主用 Agent tool 派 `seed-kit:seed-review`。简单 slice / 快速查。直接对 Claude 说"用 seed-kit:seed-review 审 S-005"。

## 模式 3（重）：agent team

Claude 自主 TeamCreate 组 architect-A/B + devil's-advocate 对抗。高价值 / 架构争议。实验性。

## 强制（每个 slice done 前必过 review-loop）

impl 做 slice → assert 绿 → 跑 `/seed-kit:review-loop` 到 converged → `seed review-mark <task> --slice <S> --verdict converged` 落 marker → `seed done`（review_gate hook 查 marker，没 converged 不准勾选）→ commit → 下一个 slice。

review_gate 是 PreToolUse **硬 gate**（不再是软提醒）：弱模型想跳过 review-loop 直接 `seed done` 会被拦，给出"先跑 review-loop + review-mark"的可执行下一步。真·卡住（review-loop 熔断/escalate）走卡住协议停下交人，不给 done 开后门。

## 为什么不用 install

Claude Code 插件不分发 workflow（`workflows/` 非插件目录）。方向 2 用 command inline 调 Workflow，绕开 install + 重启——`/seed-kit:review-loop` 一句话直接跑。
