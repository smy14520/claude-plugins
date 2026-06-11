---
name: doctor
description: "Run a project-level sdd-kit health check for Arbor packages, wiki lint, and next action. Invoke when the user asks for sdd-kit doctor, workflow health check, 项目检查, or 一键验证."
disable-model-invocation: true
allowed-tools: Bash(sdd-arbor doctor *), Bash(sdd-wiki lint *)
---

# Doctor — project health check

使用语言：中文。

Arbor helper 入口、路径和常用命令见 [`../references/arbor-helper.md`](../references/arbor-helper.md)；运行前遵守其中约定。

运行项目级健康检查（两个独立工具，各管一层）：

```bash
sdd-arbor doctor --json   # .arbor package 健康 + next action
sdd-wiki lint --json      # .wiki orientation layer 健康（.wiki 不存在时直接跳过）
```

根据两份输出汇总：

- `errors`：必须先修复的 hard error（package validation 与 wiki lint 分别报告）。
- `warnings`：建议处理但不阻断。
- `next_action`：当前最小下一步建议，可能是 brainstorm / impl / review / user / none。
- `blocked_count`：需要用户处理的阻塞数量。

不要手动重做 `validate`、`sdd-wiki lint` 或 next action 聚合逻辑；以两个 helper 的输出为准。
