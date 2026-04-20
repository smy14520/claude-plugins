---
name: task
description: "Decompose a spec (or confirmed goal) into an atomic execution plan a downstream executor can consume WITHOUT re-deciding anything. Output: `.claude/tasks/<name>.tasks.md` — atomic tasks with ID, role, dependencies, deliverable, acceptance. Two modes: strict-atomic (≤ 4h per task) and lean (coarser). Task files MUST NOT contain `[[wikilinks]]`. Does NOT auto-advance. Invoke only on explicit user request (e.g. '用 task skill 拆 <spec>')."
---

# Task — 原子化执行计划

将 spec 拆解为执行者无需再做决策即可直接执行的任务。一个任务 = 一个原子化交付物 + 一条可验证的验收标准。

## 在四阶段工作流中的定位

```
research → spec → [task] → impl
                    ↓
                    └─── 执行者仅读取此文件
```

Task 是**拆解与排序**阶段。它：

- 读取 spec（`.claude/specs/<name>.md`）或会话中的目标
- 拆解为带有稳定 ID 的原子单元
- 识别共享/公共模块（防止跨 agent 重复代码）
- 通过显式 `depends-on` DAG 排序
- 可选地为每个任务标注角色（backend/frontend/data/devops/shared），为未来的多 agent 分工做准备
- **不执行**；**不做二次决策**

## 四个原语

根据用户意图匹配使用；完整流程见 [references/workflow.md](references/workflow.md)。

### 🔨 Decompose — 拆解为原子任务

触发："拆任务 X"、"把 spec X 变成任务"、"plan X"。

> **推理节奏**：🍞 **重型**。颗粒度和边界划分直接决定下游 impl 是轻松还是痛苦。请启用扩展思考。

流程（详见 `references/workflow.md#decompose`）：

1. 确定输入源：`.claude/specs/<name>.md` 或会话中的描述
2. 询问用户：strict-atomic 还是 lean 模式（见 [references/decomposition.md](references/decomposition.md)）
3. 将 spec 拆解为单元。每个单元 = 一个交付物
4. 分配稳定 ID（`T-001`、`T-002`、…）
5. 为每个单元填写必填字段（见内容契约）

### 🧱 Identify shared — 识别公共模块

触发：在拆解过程中自动识别，或用户明确说"有哪些是公共模块"。

> **推理节奏**：🍞 **重型**。公共模块识别错误是并行 impl 冲突的首要来源。请仔细思考。

流程：

1. 扫描任务中的重复关注点（例如 3 个任务都调用同一个 HTTP 客户端）
2. 为每个公共模块提取一个 `shared-module` 任务
3. 让消费任务 `depends-on` 该 shared-module 任务
4. 如果提取数量过多则提醒用户（信号：可能过度拆解）

### 🔗 Order — 构建依赖 DAG

触发：在拆解过程中自动构建，或用户明确说"排一下依赖"。

> **推理节奏**：🍞 **重型**。需要做环路检测和关键路径梳理。当 DAG 包含超过 6 个任务时，请启用扩展思考。

流程：

1. 为每个任务确定 `depends-on: [IDs]`
2. 检测环路 → 如存在，报告并阻止定稿
3. 输出依赖图（文本树或 mermaid，不要花哨）

### 🏷️ Assign role — 可选的多 agent 标注

触发：用户说"按角色分"、"tag roles"，或预期将进行多 agent 实施时。

> **推理节奏**：🥐 **轻型**。从固定角色列表中做机械分类即可。

流程：

1. 为每个任务建议角色：`backend` | `frontend` | `data` | `devops` | `shared` | `test`
2. 用户确认/修改
3. 角色仅供参考，不具约束力——当前 impl 以单 agent 运行

## 目录结构

```
.claude/tasks/
├── <spec-name>.tasks.md      # 从 spec 派生时，名称与 spec 一致
└── <ad-hoc-name>.tasks.md    # 无 spec 直接拆解时使用
```

文件命名规则：

- 从 spec 派生：与 spec 同名的 kebab-case 名称 + `.tasks.md` 后缀
- 临时拆解：用户提供或推断的 kebab-case 名称 + `.tasks.md`

## 核心规则

1. **任务文件中禁止 wikilinks** — 任务执行计划必须自包含。执行者仅读取此文件。Wiki 引用属于 spec，不属于 task。
2. **任务中禁止决策** — 每个任务有具体的交付物和可验证的验收标准。如果某个任务是"决定如何做 X"，这是 spec 阶段的职责，不是 task 的。应退回 spec。
3. **稳定 ID** — 一旦分配，任务 ID 永不更改。插入新任务使用新 ID，而非重新编号。
4. **理想情况一次提交** — strict-atomic 模式：每个任务恰好产出一个交付物（一个文件、一个接口、一个迁移）。Lean 模式：放宽为"一个逻辑单元"，但仍需可验证。
5. **验收标准必须可验证** — 每个任务必须列出：(a) 将变更的文件，(b) 验证命令（`pnpm test`、`curl …` 等）。
6. **公共模块优先** — 如果 T-004 依赖公共模块 T-001，T-001 必须排在前面。
7. **不自动推进** — 任务文件写入后，skill 即停止。Impl 需要单独调用。
8. **仅使用封闭动词** — 每个任务的交付物使用 `CREATE | ADD | SET | DELETE | REPLACE` 并附带具体目标值。开放动词（`校准 / 保持 / 验证 / 确保 / 适配`）意味着上游存在未解决的值——应作为 `<TODO-DECIDE>` 退回 spec，不要为 impl 编写模糊的任务。

## 模式选择（strict-atomic vs lean）

需明确询问用户。默认值：

- **Strict-atomic**（多人或多 agent 实施时的默认选择）：
  - 每个任务 ≤ 4 小时，单次提交，单一交付物
  - 规范程度更高，更适合并行
- **Lean**（单人快速实施时的默认选择）：
  - 任务可跨 1 天，涉及多个文件
  - 规范程度较低，编写更快，但不太适合并行

详见 [references/decomposition.md](references/decomposition.md)。

## 初始化

如果 `.claude/tasks/` 不存在，首次使用时静默创建。

## 本 skill 不做的事

- 不执行任务 — 使用 `impl` skill
- 不重新决策设计问题 — 退回 `spec`
- 不读取 wiki — 任务文件自包含，wiki 上下文留在 spec 中
- 不跟踪进度/变更任务状态 — 这是 `impl` 通过状态行负责的
- 不自动触发 impl

## 何时不应激活

- 用户想修一个一行 bug — 跳过 task，直接进入 impl
- Spec 不完整（`status: draft`，含有 `TODO-DECIDE`）— 先定稿 spec
- 用户仍在确定范围 — 使用 `spec` skill
- 已存在且仍有效的任务文件 — 读取它，不要重做

## 反模式

详见 [references/anti-patterns.md](references/anti-patterns.md)。快速列表：

- 需要执行者去读 spec 的任务
- 包含 `[[wikilinks]]` 的任务
- 要求"调查 X"的任务（那是 research）
- 包含"决定 Y"的任务（那是 spec）
- 对琐碎工作的过度拆解（一个 30 行 PR 拆出 3 个任务）
- 缺少 `depends-on` 声明（执行者只能猜测顺序）
- 不可验证的验收标准（"看起来没问题"）
