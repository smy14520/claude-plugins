# github/spec-kit

- URL: https://github.com/github/spec-kit
- 类型: AI 时代的 spec-driven development toolkit
- 收集日期: 2026-04-22

## 原始要点

- 仓库自述为“Toolkit to help you get started with Spec-Driven Development”。
- 核心观念是让开发者聚焦产品场景与可预测结果，而不是把需求散落在聊天里。
- 典型工作流由一组 slash commands 驱动：
  - `/speckit.constitution`：建立项目原则与约束
  - `/speckit.specify`：产出 feature 的 `spec.md`，强调 what / why
  - `/speckit.plan`：产出 `plan.md`，映射到具体技术方案
  - `/speckit.tasks`：从 plan 生成依赖有序的任务
  - `/speckit.implement`：按任务实施
- DeepWiki 对其结构化总结指出，主要工件包括：`constitution.md`、`spec.md`、`plan.md`、`research.md`、`data-model.md`、`contracts/`、`quickstart.md`、`tasks.md`。
- DeepWiki 还指出其关键特征是：
  - 将 spec 视为可执行资产，而不是写完即弃的文档
  - 强化 `spec.md`（技术无关）与 `plan.md`（技术相关）的边界
  - 通过模板和命令确保阶段化产出
  - 允许定义多步、可恢复的 workflow

## 对 workflow 结构的直接观察

- 这是一个明显的“多工件串联”模型，而不是单一 spec 文件。
- 它把项目原则（constitution）放在 feature spec 之前，说明它把“全局治理”与“单次需求”分层处理。
- 它强调 spec 与 implementation 之间有明确中介层：plan / tasks。
- 它比较适合把模糊需求逐步冻结为更强约束的执行工件。

## 证据摘录

> Spec-Driven Development flips the script on traditional software development.

> Use the `/speckit.specify` command to describe what you want to build. Focus on the what and why.

> Core commands: constitution → specify → plan → tasks → implement.

## 适合后续比较的维度

- 是否把项目级原则与 feature 级规范分开
- spec / plan / tasks 的边界是否清晰
- 是否存在显式阶段门与命令化工作流
- 是否偏重新项目 / 大 feature，而非轻量增量修改
