# tinder-kit

次世代工程 Coding Agent 框架：原子技能解耦、任务级隔离（`.forge`）、上下文防爆交接与 `/develop` 端到端无缝编排。

## 目录与架构

- **专属运行时目录**：`.forge/tasks/<task-slug>/`
  - `state.json`：任务级极简状态机（不绑 Git 分支，支持多任务并发）
  - `spec.md`：需求规格与商定的深接缝（Seams）
  - `handoffs/`：各阶段交接文档链（物理压缩上下文）
  - `endorsement.md`：最终交付的测试与规范背书报告
- **技能体系**：
  - **User-invoked**：编排流（`/develop` 等，面向开发者场景）
  - **Model-invoked**：原子工程素养（`tdd`, `codebase-design`, `diagnose`, `prototype` 等，模型自主调用）
  - **Bridge**：`handoff`（既可用户随时调用，又负责编排阶段间的信标交接）
