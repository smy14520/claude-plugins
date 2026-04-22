# Fission-AI/OpenSpec

- URL: https://github.com/Fission-AI/OpenSpec
- 类型: AI coding assistant 的 spec-driven workflow framework
- 收集日期: 2026-04-22

## 原始要点

- 仓库自述为“Spec-driven development (SDD) for AI coding assistants.”
- 核心哲学强调：
  - fluid not rigid
  - iterative not waterfall
  - easy not complex
  - built for brownfield not just greenfield
- README 展示的典型流程：
  - `/opsx:propose` → 创建 change 目录与 proposal / specs / design / tasks
  - `/opsx:apply` → 按 tasks 实施
  - `/opsx:archive` → 归档 change，并把 specs 更新回主线
- DeepWiki 总结的核心目录结构：
  - `openspec/specs/`：系统当前行为的 source of truth
  - `openspec/changes/<change>/proposal.md`
  - `openspec/changes/<change>/specs/`：delta specs
  - `openspec/changes/<change>/design.md`
  - `openspec/changes/<change>/tasks.md`
- DeepWiki 指出它的阶段边界不是固定 phase，而是由 artifact dependency graph 决定：某个 artifact 依赖满足时为 READY，存在时为 DONE。
- 其重要机制包括：delta specifications、schema-driven workflow、dynamic instructions、validation pipeline。

## 对 workflow 结构的直接观察

- OpenSpec 的关键不是“文档多”，而是“当前规格”和“变更规格”分层。
- 它天然适合 brownfield：先有现状 specs，再围绕 change 维护 proposal / delta specs / design / tasks。
- 与更线性的 spec-kit 相比，它更强调可回改、可迭代，而不是一次性锁死阶段。
- 它把 archive 作为正式环节，说明它重视变更闭环与规格回写。

## 证据摘录

> OpenSpec adds a lightweight spec layer so you agree on what to build before any code is written.

> Each change gets its own folder with proposal, specs, design, and tasks.

> Work fluidly — update any artifact anytime, no rigid phase gates.

## 适合后续比较的维度

- 是否区分 system-of-record specs 与 per-change specs
- 是否支持增量变更与归档回写
- 阶段是否由 artifact 依赖驱动，而非固定顺序
- 对 brownfield 项目的适配度
