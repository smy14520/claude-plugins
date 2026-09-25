---
name: develop
description: "端到端工程交付编排：按照 ask-matt 主航道自动推进“访谈 -> 规格/工单 -> 实现 -> 审查”，在关键决策点等待人类确认。"
disable-model-invocation: true
---

# Develop — 端到端开发主航道

将 ask-matt 主航道（idea -> ship）从被动建议转化为自动化推进编排。

## 执行流程

### 1. 路由与断点检查
- 从参数解析 task slug（未提供则从需求推导简短小写 slug，如 `todo-cli`）；
- 检查 `.forge/tasks/<slug>/state.json`：
  - 若已处于 `WAITING_CONFIRM`：展示已有接缝与边界，进入人类把关点 1；
  - 若已处于 `IMPLEMENTING`：从实现阶段接续，运行测试并继续推进；
  - 若为新任务：创建任务目录，初始化 `state.json`（phase: `ALIGNING`）。

### 2. 需求访谈与打磨（Align）
- 自动执行 `grill-with-docs`：
  - 驱动决策树追问（grilling）与领域建模（domain-modeling）；
  - 查证代码库事实，将业务决策沉淀至 `.forge/CONTEXT.md` 与 ADR；
- **分支：能否在对话中解决所有问题？**
  - 若遇 UI 交互手感或关键技术卡点需要可运行答案：通过 `prototype` 探针绕行，并以 `handoff` 桥接经验结论；
- 访谈收敛后，梳理出约定接缝（Agreed Seams）与明确排除项（Out of Scope）。

### 3. 规格决策与把关（Branch: multi-session?）
- **🛑 人类把关点 1**：在终端呈递方案核心接缝与边界，根据任务规模由人类确认推进方式：
  - **单会话需求**（无需跨会话拆工单）：确认后直接在当前上下文进入实现；
  - **多会话大工程**：调用 `/to-spec` 沉淀 spec，并调用 `/to-tickets` 拆分为带依赖关系的工单；
  - 提示人类：“需求与接缝已对齐。请确认开工（直接开工 / 拆工单 / 调整意见）？”
  等待人类确认。确认后更新 `state.json`（phase: `IMPLEMENTING`）。

### 4. 编码实现（Implement）
- 自动推进 `implement`：在预定 seams 上驱动 `tdd`（一次一个 red-green slice，断言公共行为）；
- 跑通完整自动化测试套件。

### 5. 双轴审查与交付（Review）
- 自动执行 `code-review`：对改动进行 Standards（规范与坏味道）与 Spec（需求与 Seams 兑现度）双轴客观审查；
- 更新 `state.json`（phase: `COMPLETED`）；
- **🛑 人类把关点 2**：呈递双轴审查结论与测试通过证据，交还控制权：
  > “测试全绿，双轴审查已通过。请审查 git diff 并执行 commit。”
