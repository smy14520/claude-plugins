# create-conductor-flow / Conductor

- URL: https://github.com/Jonkimi/create-conductor-flow
- 类型: context-first, portable spec-driven workflow scaffolding
- 收集日期: 2026-04-22

## 原始要点

- 项目定位是把 Gemini Conductor 风格的 spec-driven workflow 移植到多种 coding agent 环境。
- 核心口号是 “Context is King”，强调 context-first evolution of spec-driven development。
- 关键工件包括：`product.md`、`tech-stack.md`、`spec.md`、`plan.md`。
- 典型命令包括：
  - `/conductor-setup`
  - `/conductor-newTrack`
  - `/conductor-implement`
  - `/conductor-review`
  - `/conductor-revert`
  - `/conductor-status`
- 它非常强调 agent-agnostic setup / workflows：可以在 Claude Code、Cursor、Codex、Copilot 等之间迁移，而不丢 workflow context。

## 对 workflow 结构的直接观察

- 这个样本的重要价值不在“流程最成熟”，而在“把 workflow 设计成可移植层”。
- 它把 product / tech-stack 作为长期上下文工件放到 spec 前面，这与单 feature spec 流程不同。
- 对当前项目的启发是：如果希望 workflow 不绑定单一 agent，核心工件应尽量 repo-native，而不是只藏在某种工具配置里。

## 证据摘录

> Context-first evolution of spec-driven development.

> Structured artifacts (`product.md`, `tech-stack.md`, `spec.md`, `plan.md`) keep your AI agent focused and context-aware.

> Agent-agnostic workflows: switch between agents without losing project context or progress.

## 适合后续比较的维度

- 是否要引入 product / tech-stack 这类长期上下文工件
- workflow 是否需要对 agent / IDE 可移植
- 长期上下文与单次 feature spec 如何分层
