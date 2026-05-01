---
name: doctor
description: "Run a project-level sdd-kit health check for Arbor packages, wiki lint, and map readiness. Invoke when the user asks for sdd-kit doctor, workflow health check, 项目检查, or 一键验证."
disable-model-invocation: true
allowed-tools: Bash(sdd-arbor doctor *)
---

# Doctor — project health check

使用语言：中文。

运行项目级健康检查：

```bash
sdd-arbor doctor --json
```

根据 helper 输出汇总：

- `errors`：必须先修复的 hard error。
- `warnings`：建议处理但不阻断。
- `blocked packages`：当前 workflow 阻塞状态，不一定是项目错误。
- `next action`：给出最小下一步建议。

不要手动重做 `validate`、`wiki-lint`、`map-check` 的逻辑；以 `sdd-arbor doctor` 输出为准。
