---
name: task
description: "Decompose an already boundary-sized executable package PRD `.arbor/tasks/<package>/prd.md` into package-local T-xxx control/acceptance/review units. Task is a secondary guard: it refuses unchecked or split_recommended package sizing and only proceeds for fits_package/split_applied. `.arbor/tasks/<package>/` is the execution boundary; T-xxx tasks are not default branch/worktree/PR units. Invoke only on explicit user request."
---

# Task — Secondary Guard + T-xxx Decomposition

将已确认的 executable package PRD 拆解为执行者无需再做高层设计决策即可直接推进的任务计划。Package 是 branch/worktree/PR/agent ownership 的执行边界；T-xxx 是 package 内部的 control / acceptance / review 单元。

## 在五阶段工作流中的定位

```text
research → map? → brainstorm → [task] → impl
                    │           ↓
                    └── .arbor/tasks/<package>/prd.md
                                └── 执行者主要读取 task.md + task.json + context/*.jsonl
```

Task 是**执行冻结与排序**阶段。它不再作为拆 package 的主入口；主边界判断应在 brainstorm/map 完成。Task 只做 secondary guard：

- 读取 package-local PRD（首选 `.arbor/tasks/<package>/prd.md`）和 `task.json`
- 检查 `package_sizing.status`
  - `unchecked`：停止，回到 brainstorm/map 做 boundary sizing
  - `split_recommended`：停止，回到 `.arbor/maps/<initiative>/map.md` + `map.json` 和 child package PRD
  - `fits_package` / `split_applied`：继续
- 询问 strict-atomic / lean 模式
- 将当前 package 分成 milestone / slice / executable T-xxx
- 为每个 T-xxx 补齐 task-local context、sources、ready-check
- 识别共享模块，避免跨 task 重复代码
- 构建显式 `depends-on` DAG
- 使用 `tools/arbor.py` 更新 `task.json` 生命周期元数据
- 可选标注角色，为同一 package boundary 内的并行 impl 做准备
- **不执行**；**不重新做高层方案选择**

## Deterministic state layer

Task skill 负责语义拆解；`tools/arbor.py` 负责机械状态事务：

```text
python3 plugins/sdd-kit/tools/arbor.py show <package>
python3 plugins/sdd-kit/tools/arbor.py add-child <package> --id T-001 --title "ADD ..." --milestone M-01 --role shared --ready true
python3 plugins/sdd-kit/tools/arbor.py add-context <package> --type impl --task T-001 --kind constraint --summary "..."
python3 plugins/sdd-kit/tools/arbor.py freeze-definition <package> --actor task --note "task definition frozen"
python3 plugins/sdd-kit/tools/arbor.py validate <package>
```

`set-package-sizing` 默认由 brainstorm/map 调用。Task 只在迁移/恢复旧包时可补记 sizing；不要把它作为正常拆包主流程。

不要让脚本判断任务是否拆得好；也不要手写会破坏 `task.json` schema 的状态变更。

## 四个原语

### 🔨 Decompose — 从 PRD 生成执行计划

触发："拆任务 X"、"把 PRD X 变成任务"、"plan X"。

> **推理节奏**：🍞 **重型**。判断切片、上下文边界和里程碑结构时请启用扩展思考。

流程：

1. 确定输入源：
   - 首选 `.arbor/tasks/<package>/prd.md`
   - legacy fallback：若只有 `.arbor/brainstorms/<name>.md`，可读取并提示迁入 `.arbor/tasks/<package>/prd.md`；关键结论必须先摘要进 package-local PRD，后续任务不得依赖旧路径；新产物不得写回旧路径
   - 或用户在会话中确认的 ad-hoc 目标
2. 读取 `task.json`，检查 `package_sizing.status`：
   - `unchecked`：停止，要求先用 brainstorm/map 记录 `fits_package` 或 `split_applied`
   - `split_recommended`：停止，要求先创建/更新 `.arbor/maps/<initiative>/map.md` + `map.json` 并 materialize child package stubs
   - `fits_package` / `split_applied`：继续
3. 询问用户：strict-atomic 还是 lean 模式。
4. 判断是否需要 milestone / parent-child 结构：
   - 小 package：直接平铺任务
   - 大但仍单 PR 的 package：先分 milestone，再拆 package-local T-xxx
5. 为每个任务填写必填字段：`deliverable / acceptance / context / sources / ready-check`。
6. 产出/更新 `.arbor/tasks/<package>/` task package：`task.md`、`task.json`、`review.md`、`context/impl.jsonl`、`context/review.jsonl`、`context/sources.jsonl`。
7. 对每个 T-xxx 使用 `arbor.py add-child` 写入 lifecycle record；对 task-local context 使用 `arbor.py add-context`。
8. 如已规划 package branch/worktree/PR，可用 `arbor.py set-execution <package> ...` 记录 package-level execution metadata；不要给 T-xxx 写 branch/worktree/PR。
9. 使用 `arbor.py freeze-definition <package> --actor task --note "task definition frozen"` 标记 `task.md` 已冻结。
10. 运行 `arbor.py validate <package>`；失败则修正结构后再交付。

### 🧱 Identify shared — 识别共享模块与前置切片

触发：拆解过程中自动识别，或用户说"有哪些公共模块"。

> **推理节奏**：🍞 **重型**。共享模块识别错误是并行 impl 冲突的首要来源。

流程：

1. 扫描多个切片之间的重复依赖（例如共享验证器、配置加载、通用客户端）。
2. 为真正独立、可复用的共享能力提取 shared task。
3. 让消费任务显式依赖它。
4. 若 shared 任务比例过高，提示可能过度抽象。

### 🔗 Order — 构建 milestone / DAG

触发：拆解过程中自动构建，或用户说"排一下依赖"。

> **推理节奏**：🍞 **重型**。需要同时处理里程碑层级和任务 DAG。

流程：

1. 为每个任务确定 `depends-on`。
2. 检测环路；如存在，阻止定稿。
3. 输出文本依赖图和关键路径。
4. 标注哪些任务 ready，哪些仍被 open question 阻塞。
5. 使用 `arbor.py validate <package>` 做机械环路和引用检查。

### 🏷️ Assign role — 标注执行角色（可选）

触发：用户说"按角色分"、"tag roles"，或预期并行实施时。

> **推理节奏**：🥐 **轻型**。机械分类即可。

流程：

1. 为每个任务建议 `backend | frontend | data | devops | shared | test | docs | fullstack`。
2. 用户确认 / 修改。
3. 角色仅供参考，不具约束力。

## 目录结构

```text
.arbor/tasks/
└── <package-name>/
    ├── prd.md              # executable package PRD；brainstorm skill 负责
    ├── task.md             # 稳定任务定义；task skill 负责创建/追加
    ├── task.json           # 生命周期事实源；arbor.py 机械维护
    ├── review.md           # review 只追加语义审计记录
    └── context/
        ├── impl.jsonl      # 给实现阶段的轻量上下文 packet
        ├── review.jsonl    # 给审计阶段的轻量上下文 packet
        └── sources.jsonl   # 来源索引
```

## Package sizing secondary guard

Task 阶段必须先验证上游 boundary sizing：当前 PRD 是否已经被 brainstorm/map 确认为 executable package？

继续条件：

- **fits_package**：当前 package 可以对应一个 branch/worktree/PR。
- **split_applied**：当前 package 是上位 map 拆出的 executable child package。

停止条件：

- **unchecked**：没有上游 boundary decision。回到 brainstorm/map，不要写 T-xxx。
- **split_recommended**：当前输入仍是 oversized initiative。回到 `.arbor/maps/<initiative>/map.md` + `map.json`，不要写长 T-xxx。

拆 package 的常见信号（如果 task 阶段发现这些，说明上游 sizing 可能 stale，应停止）：

- 一个 PRD 覆盖多个可独立 review / merge 的业务域
- 某个 slice 自然需要独立 branch/worktree/PR 或独立发布节奏
- 预期多个 agent 可以长期并行，而不只是同一 package 内短暂协作
- T-xxx 数量会超过约 8-10 个，或关键路径很长且旁路模块明显独立
- 涉及前台 / 后台 / 交易 / 营销 / 权限等多个子系统
- 某些 slice 可以单独上线、回滚或验收

## 核心规则

1. **验证上游 package sizing** — 不得在 `package_sizing.status=unchecked` 或 `split_recommended` 时写入 T-xxx；先确认单 package 成立或回到 map。
2. **任务定义禁止 wikilinks** — `task.md` 应自包含；执行者不需要顺着链接补全上下文。
3. **任务中禁止高层决策** — 如果某个 task 本质上是"决定怎么做 X"，那是 brainstorm/PRD 的职责，不是 task 的。
4. **稳定 ID** — 一旦分配，永不重排。新增任务只追加；T-xxx 只在当前 package 内唯一。
5. **Package 是执行边界** — branch/worktree/PR/agent metadata 属于 `.arbor/tasks/<package>/`；不要为每个 T-xxx 默认创建独立执行边界。
6. **T-xxx 是控制边界** — 每个 T-xxx 承载 deliverable / acceptance / dependency / review scope；不是默认 PR 单元。
7. **任务必须有 task-local context** — 不是把执行者丢回 PRD 自己猜。
8. **任务必须有 sources** — 至少列出和该 task 相关的来源 ID，保证可追溯。
9. **ready-check 是显式的** — 只有真正阻塞此任务的 open question 才会阻止执行；不是要求上游文档零歧义。
10. **不自动推进** — 任务文件写完后停止。Impl 需要单独调用。
11. **仅使用封闭动词** — `CREATE | ADD | SET | DELETE | REPLACE`。开放动词意味着上游冻结不足。
12. **状态是结构化元数据** — 不创建 `status.md`；任务状态、当前阶段、下一步和子任务状态写入 `task.json`，避免 markdown TODO 漂移。
13. **`task.json` 是生命周期事实源** — task skill 通过 `arbor.py` 初始化 `state/current_phase/next_action/tasks[].ready/blockers/phase_history`；后续 impl/review 更新运行态。
14. **context JSONL 是索引，不是长文档** — 每行短、事实性、可定位；长解释放进 `prd.md` 或 `task.md`。
15. **helper 不同步 Markdown** — `arbor.py add-child` 只更新 `task.json`；task skill 必须把真实任务定义写实到 `task.md`，不能留下模板占位。

## 模式选择（strict-atomic vs lean）

需明确询问用户。默认值：

- **Strict-atomic**：每个 T-xxx ≤ 4 小时，单一交付物，适合在同一 package boundary 内控制并行和 review 粒度
- **Lean**：T-xxx 可到 1 天，更适合单人快速推进

## 初始化

正常情况下 `.arbor/tasks/<package>/` 已由 brainstorm 创建。如果 package 不存在，先回到 brainstorm 判断边界；不要在 task 阶段直接为 large initiative 创建目录。

## 本 skill 不做的事

- 不执行任务 —— 使用 `impl` skill
- 不重新做高层方案选择 —— 退回 `brainstorm`
- 不读取 wiki 作为执行依赖 —— 如需长期知识，由 PRD 显式摘要进 task-local context
- 不自动触发 impl
- 不创建 branch/worktree/PR；只可通过 `arbor.py set-execution` 记录 package-level metadata
- 不把多个可独立 PR/worktree 的边界硬塞进一个 package 的 T-xxx 列表
- 不为 package-local T-xxx 默认创建独立执行边界
- 不创建上位 initiative 的 `.arbor/tasks/<initiative>/`
- 不创建新的 `.arbor/brainstorms/<name>.md`

## 何时不应激活

- 用户想修一个一行 bug —— 跳过 task，直接 impl
- 用户仍在发散 / 还没形成可拆解的 executable package PRD —— 先 research 或 brainstorm
- 当前输入是 large initiative —— 用 map，不用 task
- 已存在且仍有效的 task package —— 读取并续用，不重做

## 输入说明

- 首选输入：`.arbor/tasks/<package>/prd.md`
- Legacy fallback：`.arbor/brainstorms/<name>.md` 只可作为读取/迁入来源；有效内容必须显式迁入 `prd.md`
- 无 PRD 文件时，必须先回到 brainstorm 确认目标、范围、acceptance 和 package boundary
