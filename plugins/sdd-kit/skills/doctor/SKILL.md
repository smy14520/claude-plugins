---
name: doctor
description: "Run a project-level sdd-kit health check for Arbor packages, wiki lint, and next action. Invoke when the user asks for sdd-kit doctor, workflow health check, 项目检查, or 一键验证."
disable-model-invocation: true
allowed-tools: Bash(sdd-arbor doctor *)
---

# Doctor — project health check

使用语言：中文。

Arbor helper 入口、路径和常用命令见 [`../references/arbor-helper.md`](../references/arbor-helper.md)；运行前遵守其中约定。

运行项目级健康检查：

```bash
sdd-arbor doctor --json
```

根据 helper 输出汇总：

- `errors`：必须先修复的 hard error。
- `warnings`：建议处理但不阻断。
- `next_action`：当前最小下一步建议，可能是 brainstorm / impl / review / user / none。
- `blocked_count`：需要用户处理的阻塞数量。

不要手动重做 `validate`、`wiki-lint` 或 next action 聚合逻辑；以 `sdd-arbor doctor` 输出为准。
