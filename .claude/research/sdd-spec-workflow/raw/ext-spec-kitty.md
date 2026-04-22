# Priivacy-ai/spec-kitty

- URL: https://github.com/Priivacy-ai/spec-kitty
- 类型: 面向 AI coding agents 的 spec-driven CLI workflow
- 收集日期: 2026-04-22

## 原始要点

- 仓库定位为“Spec-Driven Development for serious software developers”，强调 Claude / Cursor / Gemini / Codex 等多 agent 适配。
- DeepWiki 总结的阶段链路为：
  - init
  - constitution
  - specify（含 discovery interview gate）
  - plan（含 planning interrogation）
  - research
  - tasks
  - implement
  - review
  - accept
  - merge
- 其工件不仅有 `spec.md` / `plan.md` / `tasks.md`，还包括：
  - `tasks/planned/WPxx-*.md` work package prompts
  - `meta.json`
  - `.worktrees/<feature>`
  - `.kittify/` workflow scripts
- 其特色机制包括：
  - mandatory interview gates
  - Kanban dashboard
  - work package lane 流转（planned / doing / for_review / done）
  - git worktree 隔离
  - acceptance 与 merge 作为正式环节

## 对 workflow 结构的直接观察

- 这是目前看到的样本里“执行治理最强”的一种。
- 它不仅关心 spec 怎么写，还把后续执行单元、review 流、acceptance、merge 都制度化了。
- 它将 task 再细化为 work package，并为每个包生成 prompt 文件，说明它把 agent 执行也纳入工作流工件。
- 相比 spec-kit / OpenSpec，它更像“带看板与 lane 的全流程 operating system”。

## 证据摘录

> Spec Kitty is an open-source CLI workflow for spec-driven development with AI coding agents.

> repeatable path: spec -> plan -> tasks -> implement -> review -> merge.

> discovery gates block progression until requirements are captured.

## 适合后续比较的维度

- 是否需要强执行治理（lane / review / accept / merge）
- task 是否继续细化为可分派 work package
- 是否把 agent prompt / worktree / dashboard 也纳入 workflow
- 这种重流程是否会超出当前项目想要的“窄职责阶段”
