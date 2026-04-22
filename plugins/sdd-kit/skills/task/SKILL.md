---
name: task
description: "Decompose a brainstorm artifact (or compatible legacy spec) into an execution-ready plan a downstream executor can consume with minimal re-decision. Output: `.claude/tasks/<name>.tasks.md` — milestones, atomic tasks, dependencies, deliverable, acceptance, task-local context, sources, and ready-check. Two modes: strict-atomic (≤ 4h per task) and lean (coarser). Task files MUST NOT contain `[[wikilinks]]`. Does NOT auto-advance. Invoke only on explicit user request (e.g. '用 task skill 拆 <brainstorm>')."
---

# Task — 执行冻结与任务拆解

将 brainstorm（或兼容 legacy spec）拆解为执行者无需再做高层设计决策即可直接推进的任务计划。它不只是原子化任务列表，还负责把大需求冻结成 milestone / child task / DAG / task-local context。

## 在五阶段工作流中的定位

```text
research → brainstorm → [task] → impl
                          ↓
                          └─── 执行者仅读取此文件
```

Task 是**执行冻结与排序**阶段。它：

- 读取 brainstorm（首选 `.claude/brainstorms/<name>.md`）或兼容 legacy spec（`.claude/specs/<name>.md`）
- 将整体 change 分成 milestone / slice / executable task
- 为每个任务补齐 task-local context、sources、ready-check
- 识别共享模块，避免跨 task 重复代码
- 构建显式 `depends-on` DAG
- 可选标注角色，为未来并行 impl 做准备
- **不执行**；**不重新做高层方案选择**

## 四个原语

### 🔨 Decompose — 从 brainstorm 生成执行计划

触发："拆任务 X"、"把 brainstorm X 变成任务"、"plan X"。

> **推理节奏**：🍞 **重型**。判断切片、上下文边界和里程碑结构时请启用扩展思考。

流程：

1. 确定输入源：
   - 首选 `.claude/brainstorms/<name>.md`
   - 兼容 `.claude/specs/<name>.md`
   - 或用户在会话中确认的目标
2. 询问用户：strict-atomic 还是 lean 模式
3. 先判断是否需要 milestone / parent-child 结构：
   - 小需求：直接平铺任务
   - 大需求：先分 milestone，再拆 child tasks
4. 为每个任务填写必填字段：`deliverable / acceptance / context / sources / ready-check`
5. 产出 `.claude/tasks/<name>.tasks.md`

### 🧱 Identify shared — 识别共享模块与前置切片

触发：拆解过程中自动识别，或用户说"有哪些公共模块"。

> **推理节奏**：🍞 **重型**。共享模块识别错误是并行 impl 冲突的首要来源。

流程：

1. 扫描多个切片之间的重复依赖（例如共享验证器、配置加载、通用客户端）
2. 为真正独立、可复用的共享能力提取 shared task
3. 让消费任务显式依赖它
4. 若 shared 任务比例过高，提示可能过度抽象

### 🔗 Order — 构建 milestone / DAG

触发：拆解过程中自动构建，或用户说"排一下依赖"。

> **推理节奏**：🍞 **重型**。需要同时处理里程碑层级和任务 DAG。

流程：

1. 为每个任务确定 `depends-on`
2. 检测环路；如存在，阻止定稿
3. 输出文本依赖图和关键路径
4. 标注哪些任务 ready，哪些仍被 open question 阻塞

### 🏷️ Assign role — 标注执行角色（可选）

触发：用户说"按角色分"、"tag roles"，或预期并行实施时。

> **推理节奏**：🥐 **轻型**。机械分类即可。

流程：

1. 为每个任务建议 `backend | frontend | data | devops | shared | test`
2. 用户确认 / 修改
3. 角色仅供参考，不具约束力

## 目录结构

```text
.claude/tasks/
├── <brainstorm-name>.tasks.md
└── <ad-hoc-name>.tasks.md
```

## 核心规则

1. **任务文件中禁止 wikilinks** — 执行者应只读一个文件完成本轮执行。
2. **任务中禁止高层决策** — 如果某个 task 本质上是"决定怎么做 X"，那是 brainstorm 的职责，不是 task 的。
3. **稳定 ID** — 一旦分配，永不重排。新增任务只追加。
4. **任务必须有 task-local context** — 不是把执行者丢回 brainstorm 自己猜。
5. **任务必须有 sources** — 至少列出和该 task 相关的来源 ID，保证可追溯。
6. **ready-check 是显式的** — 只有真正阻塞此任务的 open question 才会阻止执行；不是要求上游文档零歧义。
7. **不自动推进** — 任务文件写完后停止。Impl 需要单独调用。
8. **仅使用封闭动词** — `CREATE | ADD | SET | DELETE | REPLACE`。开放动词意味着上游冻结不足。

## 模式选择（strict-atomic vs lean）

需明确询问用户。默认值：

- **Strict-atomic**：每个任务 ≤ 4 小时，单一交付物，适合并行
- **Lean**：任务可到 1 天，更适合单人快速推进

## 初始化

如果 `.claude/tasks/` 不存在，首次使用时静默创建。

## 本 skill 不做的事

- 不执行任务 —— 使用 `impl` skill
- 不重新做高层方案选择 —— 退回 `brainstorm`
- 不读取 wiki 作为执行依赖 —— 如需长期知识，由 brainstorm 显式摘要进 task-local context
- 不自动触发 impl

## 何时不应激活

- 用户想修一个一行 bug —— 跳过 task，直接 impl
- 用户仍在发散 / 还没形成可拆解的 brainstorm —— 先 research 或 brainstorm
- 已存在且仍有效的任务文件 —— 读取并续用，不重做

## 兼容说明

- 首选输入：`.claude/brainstorms/<name>.md`
- 兼容输入：`.claude/specs/<name>.md`
- 旧 contract-style spec 仍可拆，但新 brainstorm 格式更适合大需求与来源追踪
