---
name: task
description: "Decompose a package-local PRD `.arbor/tasks/<name>/prd.md` into an execution-ready task package a downstream executor can consume with minimal re-decision. Output stays inside `.arbor/tasks/<name>/`: `task.md`, `task.json`, `review.md`, and `context/*.jsonl` — milestones, atomic tasks, dependencies, deliverable, acceptance, task-local context, sources, ready-check, and recoverable lifecycle metadata. Two modes: strict-atomic (≤ 4h per task) and lean (coarser). Task files MUST NOT contain `[[wikilinks]]`. Does NOT auto-advance. Invoke only on explicit user request (e.g. '用 task skill 拆 <package>')."
---

# Task — 执行冻结与任务拆解

将 package-local PRD 拆解为执行者无需再做高层设计决策即可直接推进的任务计划。它不只是原子化任务列表，还负责把需求冻结成 milestone / child task / DAG / task-local context。

## 在五阶段工作流中的定位

```text
research → brainstorm → [task] → impl
              │           ↓
              └── .arbor/tasks/<name>/prd.md
                          └── 执行者主要读取 task.md + task.json + context/*.jsonl
```

Task 是**执行冻结与排序**阶段。它：

- 读取 package-local PRD（首选 `.arbor/tasks/<name>/prd.md`）
- 将整体 change 分成 milestone / slice / executable task
- 为每个任务补齐 task-local context、sources、ready-check
- 识别共享模块，避免跨 task 重复代码
- 构建显式 `depends-on` DAG
- 使用 `tools/arbor.py` 初始化/更新 `task.json` 可恢复生命周期元数据（ready/blockers/current_phase/next_action/phase_history）
- 可选标注角色，为未来并行 impl 做准备
- **不执行**；**不重新做高层方案选择**

## Deterministic state layer

Task skill 负责语义拆解；`tools/arbor.py` 负责机械状态事务：

```text
python3 plugins/sdd-kit/tools/arbor.py create <name> --mode strict-atomic --title "<title>"
python3 plugins/sdd-kit/tools/arbor.py add-child <name> --id T-001 --title "ADD ..." --milestone M-01 --role shared --ready true
python3 plugins/sdd-kit/tools/arbor.py add-context <name> --type impl --task T-001 --kind constraint --summary "..."
python3 plugins/sdd-kit/tools/arbor.py freeze-definition <name> --actor task --note "task definition frozen"
python3 plugins/sdd-kit/tools/arbor.py validate <name>
```

不要让脚本判断任务是否拆得好；也不要手写会破坏 `task.json` schema 的状态变更。

## 四个原语

### 🔨 Decompose — 从 PRD 生成执行计划

触发："拆任务 X"、"把 PRD X 变成任务"、"plan X"。

> **推理节奏**：🍞 **重型**。判断切片、上下文边界和里程碑结构时请启用扩展思考。

流程：

1. 确定输入源：
   - 首选 `.arbor/tasks/<name>/prd.md`
   - legacy fallback：若只有 `.arbor/brainstorms/<name>.md`，可读取并提示迁入 `.arbor/tasks/<name>/prd.md`；关键结论必须先摘要进 package-local PRD，后续任务不得依赖旧路径；新产物不得写回旧路径
   - 或用户在会话中确认的 ad-hoc 目标
2. 若 package 不存在，先运行 `arbor.py create <name>` 初始化 `.arbor/tasks/<name>/`
3. 询问用户：strict-atomic 还是 lean 模式
4. 先判断是否需要 milestone / parent-child 结构：
   - 小需求：直接平铺任务
   - 大需求：先分 milestone，再拆 child tasks
5. 为每个任务填写必填字段：`deliverable / acceptance / context / sources / ready-check`
6. 产出/更新 `.arbor/tasks/<name>/` task package：`task.md`、`task.json`、`review.md`、`context/impl.jsonl`、`context/review.jsonl`、`context/sources.jsonl`
7. 对每个 T-xxx 使用 `arbor.py add-child` 写入 lifecycle record；对 task-local context 使用 `arbor.py add-context`
8. 使用 `arbor.py freeze-definition <name> --actor task --note "task definition frozen"` 标记 `task.md` 已冻结
9. 运行 `arbor.py validate <name>`；失败则修正结构后再交付

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
5. 使用 `arbor.py validate <name>` 做机械环路和引用检查

### 🏷️ Assign role — 标注执行角色（可选）

触发：用户说"按角色分"、"tag roles"，或预期并行实施时。

> **推理节奏**：🥐 **轻型**。机械分类即可。

流程：

1. 为每个任务建议 `backend | frontend | data | devops | shared | test | docs | fullstack`
2. 用户确认 / 修改
3. 角色仅供参考，不具约束力

## 目录结构

```text
.arbor/tasks/
└── <package-name>/
    ├── prd.md              # package-local PRD；brainstorm skill 负责
    ├── task.md             # 稳定任务定义；task skill 负责创建/追加
    ├── task.json           # 生命周期事实源；arbor.py 机械维护
    ├── review.md           # review 只追加语义审计记录
    └── context/
        ├── impl.jsonl      # 给实现阶段的轻量上下文 packet
        ├── review.jsonl    # 给审计阶段的轻量上下文 packet
        └── sources.jsonl   # 来源索引
```

## 核心规则

1. **任务定义禁止 wikilinks** — `task.md` 应自包含；执行者不需要顺着链接补全上下文。
2. **任务中禁止高层决策** — 如果某个 task 本质上是"决定怎么做 X"，那是 brainstorm/PRD 的职责，不是 task 的。
3. **稳定 ID** — 一旦分配，永不重排。新增任务只追加。
4. **任务必须有 task-local context** — 不是把执行者丢回 PRD 自己猜。
5. **任务必须有 sources** — 至少列出和该 task 相关的来源 ID，保证可追溯。
6. **ready-check 是显式的** — 只有真正阻塞此任务的 open question 才会阻止执行；不是要求上游文档零歧义。
7. **不自动推进** — 任务文件写完后停止。Impl 需要单独调用。
8. **仅使用封闭动词** — `CREATE | ADD | SET | DELETE | REPLACE`。开放动词意味着上游冻结不足。
9. **状态是结构化元数据** — 不创建 `status.md`；任务状态、当前阶段、下一步和子任务状态写入 `task.json`，避免 markdown TODO 漂移。
10. **`task.json` 是生命周期事实源** — task skill 通过 `arbor.py` 初始化 `state/current_phase/next_action/tasks[].ready/blockers/phase_history`；后续 impl/review 更新运行态。
11. **context JSONL 是索引，不是长文档** — 每行短、事实性、可定位；长解释放进 `prd.md` 或 `task.md`。
12. **helper 不同步 Markdown** — `arbor.py add-child` 只更新 `task.json`；task skill 必须把真实任务定义写实到 `task.md`，不能留下模板占位。

## 模式选择（strict-atomic vs lean）

需明确询问用户。默认值：

- **Strict-atomic**：每个任务 ≤ 4 小时，单一交付物，适合并行
- **Lean**：任务可到 1 天，更适合单人快速推进

## 初始化

如果 `.arbor/tasks/<name>/` 不存在，先运行 `tools/arbor.py create`。如果 package 已存在且仍有效，读取并续用，不重做。

## 本 skill 不做的事

- 不执行任务 —— 使用 `impl` skill
- 不重新做高层方案选择 —— 退回 `brainstorm`
- 不读取 wiki 作为执行依赖 —— 如需长期知识，由 PRD 显式摘要进 task-local context
- 不自动触发 impl
- 不创建新的 `.arbor/brainstorms/<name>.md`

## 何时不应激活

- 用户想修一个一行 bug —— 跳过 task，直接 impl
- 用户仍在发散 / 还没形成可拆解的 PRD —— 先 research 或 brainstorm
- 已存在且仍有效的 task package —— 读取并续用，不重做

## 输入说明

- 首选输入：`.arbor/tasks/<name>/prd.md`
- Legacy fallback：`.arbor/brainstorms/<name>.md` 只可作为读取/迁入来源；有效内容必须显式迁入 `prd.md`
- 无 PRD 文件时，必须先在会话中确认目标、范围和 acceptance，再创建 ad-hoc task package
