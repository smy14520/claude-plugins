# claude-plugins

个人 Claude Code 插件市场，当前专注于 **seed-kit**。

## seed-kit

轻量 PRD-first 工作流：research / brainstorm / impl / review / wiki 五个 skill 全部由用户主动触发、互不自动耦合。状态就是 `prd.md` 的 slice checkbox + `evidence/` 证据文件，没有状态机、没有 task.json。

核心验证哲学：**gate 守对错（正确性，二值断言），loop 守好坏（质量，judge 迭代到收敛）**——刻意不把体验质量塞进二值 gate（Goodhart：优化“verdict 变绿”≠“体验变好”）。

详见：

- 设计动机与取舍 → [`plugins/seed-kit/DESIGN.md`](./plugins/seed-kit/DESIGN.md)
- 快速上手、命令面、安装 → [`plugins/seed-kit/README.md`](./plugins/seed-kit/README.md)

## 市场清单

市场注册在 [`.claude-plugin/marketplace.json`](./.claude-plugin/marketplace.json)。

## 开发

```bash
cd plugins/seed-kit && python3 -m pytest tests/ -q   # 跑插件测试
```
