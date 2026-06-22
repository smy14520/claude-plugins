# review 的三种模式

review SKILL 只管"审什么"（知识）。执行走三种模式之一，由用户指定或 Claude 按场景——**编排不在 review SKILL**。

## 模式 2（默认）：`/seed-kit:review-loop` command

最简单——**不用 install、不用重启**。在加载了 seed-kit 的项目里：

```
/seed-kit:review-loop S-005
```

command 读 `templates/review-loop.template.js` + 用 Workflow 工具跑（审代码/产物 + propose-kill 3 票证伪 + 客观 assert 锚，loop 到收敛或熔断）。

## 模式 1（轻）：subagent

Claude 自主用 Agent tool 派 `seed-kit:seed-review`。简单 slice / 快速查。直接对 Claude 说"用 seed-kit:seed-review 审 S-005"。

## 模式 3（重）：agent team

Claude 自主 TeamCreate 组 architect-A/B + devil's-advocate 对抗。高价值 / 架构争议。实验性。

## 自动触发（每个 slice 完成 → review）

impl 做 slice → `seed done` → impl 流程指向 `/seed-kit:review-loop` + hook 提醒 → 主 session 跑 command → 审 → 收敛 → 下一个 slice。

注意：hook 不能硬跑 workflow/command（只能提醒/注入），所以是"软自动"——流程 + 提醒驱动，主 session 执行。

## 为什么不用 install

Claude Code 插件不分发 workflow（`workflows/` 非插件目录）。方向 2 用 command inline 调 Workflow，绕开 install + 重启——`/seed-kit:review-loop` 一句话直接跑。
