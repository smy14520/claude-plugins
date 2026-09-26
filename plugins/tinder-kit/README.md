# tinder-kit

次世代工程 Coding Agent 框架：原子技能解耦、任务级隔离（`.forge`）、上下文隔离交接与 `/develop` 端到端无缝编排。

## 目录与架构

- **专属运行时目录**：`.forge/<slug>/`（与 setup 的 issue-tracker 契约同一目录）
  - `state.json`：任务对齐记录（原始需求、agreed seams、out of scope、关键决策），接续与审查的依据；不绑 Git 分支，支持多任务并发
  - `spec.md`：需求规格与商定的 Seams 契约
  - `issues/`：to-tickets 拆出的票（每票一个文件）
  - `handoff.md`：跨会话交接文档（单文件覆盖）
  - `endorsement.md`：最终交付的测试与规范审查报告
- **技能体系**：
  - **User-invoked**：流程入口（`/develop` 等）；`/develop` 沿 ask-matt 路线图直接调用可编排阶段（`grill-with-docs` → `to-spec` / `to-tickets` → `implement` 等）
  - **Model-invoked**：原子工程素养（`tdd`, `codebase-design`, `diagnose`, `prototype` 等，模型自主调用）
  - **Bridge**：`handoff`（既可用户随时调用，又负责编排阶段间的交接）
