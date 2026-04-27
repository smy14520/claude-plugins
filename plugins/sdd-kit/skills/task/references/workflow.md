# Task 工作流：拆分 / 识别共享 / 排序 / 分配角色

四个原语的详细流程。SKILL.md 给出高层步骤；本文件给出包含边界情况的完整工作流。

---

## 拆分

将 package-local PRD 拆解为 milestone + package-local executable T-xxx。Package 是 branch/worktree/PR 执行边界；T-xxx 是 control / acceptance / review 边界。

### 触发短语

- "拆任务 X" / "把 PRD X 变成任务"
- "plan X" / "break down package X"
- "生成 task 计划"

### 完整流程

**步骤 1 — 解析输入**

情况 A：`.arbor/tasks/<name>/prd.md` 存在

- 读取。检查前置元数据：
  - `ready-for-task` → 继续
  - `draft` / `revising` → 允许继续，但只冻结不被其 open question 阻塞的任务
  - `superseded` → 询问是否改用新 package

情况 B：只有 legacy `.arbor/brainstorms/<name>.md` 存在

- 作为 legacy input 读取
- 提示迁入 `.arbor/tasks/<name>/prd.md`
- 将仍然有效的目标、范围、场景、约束、sources 显式摘要进 package-local `prd.md`
- 后续 task/impl/review 不得依赖旧路径；新建/更新只写 package-local 文件，不再写 `.arbor/brainstorms/<name>.md`

情况 C：无文件，用户给出会话内目标

- 先回到 brainstorm 做 boundary routing，确认它不是 large initiative
- 仅当会话目标已被确认是 executable package，且目标与 acceptance 足够明确时，才可创建 ad-hoc task package：`python3 plugins/sdd-kit/tools/arbor.py create <name> --source-type ad-hoc`
- ad-hoc package 仍必须先记录 `fits_package` 或 `split_applied`，再进入 T-xxx

**步骤 2 — Package sizing secondary guard**

先读取 `task.json.package_sizing.status`，验证 brainstorm/map 是否已经确认当前 PRD 是 executable package boundary（一个 branch/worktree/PR/agent ownership 单元）。

继续条件：

- `fits_package`：当前 package 可作为一个 branch/worktree/PR。
- `split_applied`：当前 package 是 `.arbor/maps/<initiative>/map.md` 拆出的 child package。

停止条件：

- `unchecked`：停止，不写 T-xxx；回到 brainstorm/map 记录 boundary decision。
- `split_recommended`：停止，不写 T-xxx；回到 `.arbor/maps/<initiative>/map.md`，materialize child package stubs，再分别做 package-local brainstorm。

若 task 阶段发现以下信号，说明上游 boundary sizing 可能 stale，应停止并路由回 brainstorm/map：

- 覆盖多个可独立 review / merge 的业务域
- 某个 slice 自然需要独立 branch/worktree/PR 或独立发布节奏
- 多个 agent 可以长期并行而非只在同一 package 内短暂协作
- T-xxx 会超过约 8-10 个，或关键路径很长且旁路模块明显独立
- 涉及前台 / 后台 / 交易 / 营销 / 权限等多个子系统
- 某些 slice 可以单独上线、回滚或验收

**步骤 3 — 询问模式**

```text
📋 拆任务模式:
  (a) strict-atomic — 每个 T-xxx ≤ 4h, 单一 deliverable, 适合同一 package boundary 内的并行 / 多 agent
  (b) lean          — 任务可到 1 天, 适合单人快速推进
  默认: (a) strict-atomic
```

**步骤 4 — 决定是否需要 milestone**

仅在 package 边界成立后判断 milestone。

若 PRD 中出现以下信号，先分 milestone：
- 多个交付物簇
- 多个切片 / 阶段
- 明显的前后顺序
- 跨 backend / frontend / data / docs，但仍属于同一个 PR/worktree 边界

否则，直接生成平铺任务列表。

**步骤 5 — 生成任务草稿**

从以下区块推导：
- 关键场景 / 用户流
- 交付物清单
- 拆解线索 / 实现切片建议
- 风险 / 开放问题 / 假设
- Sources

每个任务至少填写：
- `id`
- `milestone`
- `role`
- `title`
- `deliverable`
- `depends-on`
- `context`
- `sources`
- `ready-check`
- `acceptance`
- `estimate`
- `notes`

**步骤 6 — 输出草稿供确认**

在用户确认前先给出任务草稿摘要。确认后再写入 `.arbor/tasks/<name>/` task package：

```text
.arbor/tasks/<name>/
├── prd.md
├── task.md
├── task.json
├── review.md
└── context/
    ├── impl.jsonl
    ├── review.jsonl
    └── sources.jsonl
```

- `prd.md`：executable package PRD/context artifact；brainstorm skill 创建/维护
- `task.md`：稳定任务定义；task skill 创建/追加，impl/review 不改
- `task.json`：package-local 生命周期状态源；由 `tools/arbor.py` 机械维护 ready/blockers/dependencies/lifecycle/package execution metadata；large initiative 统筹状态由 `.arbor/maps/<initiative>/map.json` 读取这些 child `task.json` 聚合
- `review.md`：review 追加四状态语义审计记录；不作为当前 review 状态源
- `context/*.jsonl`：阶段特定轻量上下文 packet；跨 package 多 agent 时由 `map-plan-agents` 显式列入主会话 lead / Agent Team worker context injection packet
- `context/worker-dispatch.md`：`parallel` 为当前 package worker 生成的 Trellis-like dispatch/context packet
- `status.md`：已废弃，新的 task package 不得创建

**步骤 7 — 同步机器状态**

对每个 T-xxx，调用：

```text
python3 plugins/sdd-kit/tools/arbor.py add-child <name> --id T-001 --title "ADD ..." --milestone M-01 --role shared --depends-on "" --ready true
```

对阶段上下文，调用：

```text
python3 plugins/sdd-kit/tools/arbor.py add-context <name> --type impl --task T-001 --kind constraint --source SRC-LOCAL-001 --summary "..."
python3 plugins/sdd-kit/tools/arbor.py add-context <name> --type review --task T-001 --kind acceptance --source SRC-RES-001 --summary "..."
```

如已规划 package branch/worktree/PR，可记录 package-level execution metadata（不创建资源）：

```text
python3 plugins/sdd-kit/tools/arbor.py set-execution <name> --status unclaimed --base-branch main --branch arbor/<name> --actor task --note "package execution boundary planned"
```

最后冻结任务定义并校验：

```text
python3 plugins/sdd-kit/tools/arbor.py freeze-definition <name> --actor task --note "task definition frozen"
python3 plugins/sdd-kit/tools/arbor.py validate <name>
```

### 边界情况

**情况：PRD 仍有开放问题**

不要机械阻断。只要某个问题不阻塞某个具体任务，就允许继续拆解。把阻塞写进该任务的 `ready-check`，并用 `add-child --ready false --blocker "..."` 记录到 `task.json`。

**情况：PRD 太空，无法拆分**

提示用户回到 brainstorm 补充：
- 关键场景
- 交付物清单
- 拆解线索

**情况：来源太多**

只保留和该任务直接相关的 `SRC-*`。不要把整个 PRD 附录复制进每个任务。

---

## 识别共享

查找任务间重复关注点；提取为共享模块任务。

### 流程

1. 扫描多个任务的 deliverable / context
2. 找出真正复用、且可以独立验证的共享能力
3. 创建 `role: shared` 任务
4. 消费任务追加 `depends-on`
5. 若 shared 任务超过总数的 30%，提示可能过度抽象

---

## 排序

构建 milestone 与 `depends-on` DAG。

### 流程

1. 收集所有依赖边
2. 环检测
3. 输出 ASCII 依赖图
4. 输出关键路径、可并行分支、当前 ready 任务列表
5. 使用 `arbor.py validate <name>` 做机械引用和环检测

---

## 分配角色

标准角色：
- `backend`
- `frontend`
- `data`
- `devops`
- `shared`
- `test`
- `docs`
- `fullstack`

如用户未指定，可自动建议。
