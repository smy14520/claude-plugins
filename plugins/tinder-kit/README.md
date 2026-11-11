# tinder-kit

次世代工程 Coding Agent 框架：原子技能解耦、任务级隔离（`.forge`）、上下文隔离交接与 `/develop` 端到端无缝编排。

## 目录与架构

- **`.forge/` 目录分工**：
  - `CONTEXT.md` 与 `wiki/`：跨会话长期记忆（领域术语、ADR 决策、避坑记录）
  - `scratch/`：自忽略的临时工作草稿（`.forge/scratch/.gitignore` 为 `*`），长程执行期使用，完工即删
  - `<slug>/`：`/develop` 与 `/wayfinder` 按需使用的本地任务目录（`state.json`、`spec.md`、`issues/`、`handoff.md`）
- **技能体系**：
  - **User-invoked**：流程入口（`/develop`、`/retro` 等）；`/develop` 沿 ask-matt 路线图直接调用可编排阶段（`grill-with-docs` → `to-spec` / `to-tickets` → `implement` / `implement-spec` 等）
  - **Model-invoked**：原子工程素养（`tdd`, `codebase-design`, `diagnose`, `prototype` 等，模型自主调用）
  - **Bridge**：`handoff`（既可用户随时调用，又负责编排阶段间的交接）
