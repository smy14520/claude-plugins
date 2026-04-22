# forrestchang/andrej-karpathy-skills

- URL: https://github.com/forrestchang/andrej-karpathy-skills
- 类型: Claude Code 行为准则 / instruction pack
- 收集日期: 2026-04-22

## 原始要点

- 仓库定位是：用一个 `CLAUDE.md` 文件改善 Claude Code 行为，来源于 Andrej Karpathy 对 LLM coding 常见问题的观察。
- 它明确针对的问题包括：
  - 模型会替用户做错误假设
  - 不会管理自己的困惑
  - 不主动暴露 tradeoff 或 push back
  - 容易过度工程化
  - 会误改不理解的注释或旁支代码
- 解决方式不是引入完整 workflow，而是用四条原则约束 agent 行为：
  1. Think Before Coding
  2. Simplicity First
  3. Surgical Changes
  4. Goal-Driven Execution
- 安装方式包括：
  - 作为 Claude Code plugin 安装
  - 作为项目内 `CLAUDE.md` 追加
- 它还提供 Cursor 规则文件，说明同一原则可跨工具复用。

## 对 workflow 结构的直接观察

- 这个仓库不是 spec-driven workflow 框架，而是“agent 行为约束层”。
- 它的价值在于纠正 AI coding 的常见失真：瞎猜、过度复杂化、顺手乱改、没有可验证目标。
- 它更像 workflow 的底层宪法或 coding principles，而不是 task/spec/handoff 体系。
- 因为它是单文件原则包，它也暴露出一个边界：仅靠 instruction 很难承载完整的任务状态、上下文与审计链。

## 证据摘录

> A single `CLAUDE.md` file to improve Claude Code behavior.

> Think Before Coding / Simplicity First / Surgical Changes / Goal-Driven Execution.

> The goal is reducing costly mistakes on non-trivial work, not slowing down simple tasks.

## 适合后续比较的维度

- workflow 中哪些内容适合放在“全局行为规则层”
- 原则文件能解决哪些问题，不能解决哪些问题
- 何时需要从单文件规则升级为 repo-native specs/tasks/workflow
- goal-driven execution 是否可作为 spec/task/impl 阶段的通用底层原则
