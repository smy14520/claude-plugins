# claude-plugins

个人 Claude Code 插件市场，当前专注于 **seed-kit**。

## seed-kit

轻量 PRD-first 工作流：十个 skill（research / brainstorm / wayfinder / impl / impl-agent / check / review / wiki / init / handoff）全部由用户主动触发、互不自动耦合。`prd.md` 的 slice checkbox 表示进度；`seed done` 重放显式测试/质量命令并写 `done-logs/`，显式 review-loop 可记录 task 级终态。没有 `evidence/`、task.json 或阶段状态机。

核心验证哲学：**gate 守对错（正确性，二值断言），loop 守好坏（质量，judge 迭代到收敛）**——刻意不把体验质量塞进二值 gate（Goodhart：优化“verdict 变绿”≠“体验变好”）。

详见：

- 设计动机与取舍 → [`plugins/seed-kit/DESIGN.md`](./plugins/seed-kit/DESIGN.md)
- 快速上手、命令面、安装 → [`plugins/seed-kit/README.md`](./plugins/seed-kit/README.md)
- 行为评估（seed-kit-evals 怎么用）→ [`plugins/seed-kit/EVALS.md`](./plugins/seed-kit/EVALS.md)

## 市场清单

市场注册在 [`.claude-plugin/marketplace.json`](./.claude-plugin/marketplace.json)。

## 开发

```bash
cd plugins/seed-kit && python3 -m pytest tests/ -q   # 跑插件测试
```
