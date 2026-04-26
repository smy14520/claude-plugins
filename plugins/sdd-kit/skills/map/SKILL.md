---
name: map
description: "Maintain `.arbor/maps/<initiative>/` as the canonical coordination layer for large initiatives that split into executable task packages. Materializes child package stubs, maintains map.md/map.json, and checks ready/blocked package state; Trellis-like dispatch is the separate `parallel` skill. Does NOT create T-xxx or replace package-local PRDs. Invoke only on explicit user request."
---

# Map — Large Initiative / Package Graph

维护 `.arbor/maps/<initiative>/`。其中 `map.md` 是人类导航与 contract 说明，`map.json` 是机器可读的 package graph / dependency / status / agent assignment context 源。Map 是大项目的统筹层：当一个上位主题自然拆成多个 executable task packages 时，用它记录 package graph、execution waves、跨 package contract、依赖、ready/blocked 状态与推荐下一步。

```text
research → [map?] → brainstorm package → task → impl → review
             ↑            │
             └────────────┘  package status / blocker 回写到 map
```

`map` 是 large initiative 的 canonical home。small / medium case 不需要强行创建 map。

## 定位

Map 不是 research，也不是 PRD：

- research 记录探索过程、raw evidence、notes 与 readiness。
- brainstorm 冻结一个 executable package 的 package-local PRD/context：`.arbor/tasks/<package>/prd.md`。
- map 维护多个 executable packages 之间的结构、依赖、执行 waves 和 cross-package contracts。
- map 在 package graph 确认后 materialize child package stubs：`.arbor/tasks/<package>/`。
- package 是跨域并行、branch/worktree/PR/agent ownership 的默认执行边界。

**重要**：不要为上位 initiative 创建 `.arbor/tasks/<initiative>/`。只有 map 中列出的 executable package 节点才应该变成 `.arbor/tasks/<package>/`，且只创建 package stub，不创建 T-xxx。

## 和 parallel 的分工

Map 负责创建和维护大项目 package graph：`map.md` 解释结构、依赖、execution waves 和跨 package contract；`map.json` 作为机器可读状态源，同步 child package 的 `task.json` 摘要。

Trellis-like 并行推进不再通过 verbose 的 map 参数暴露给用户；默认入口是：

```text
/sdd-kit:parallel
/sdd-kit:parallel <initiative>
用 parallel skill
并行推进 <initiative>
```

`parallel` skill 会内部执行 `map-check` / `map-plan-agents`，并只对 ready packages 启动 autonomous package pipeline worker。Map 仍可在 check/update 场景下使用 deterministic helper 查看状态，但不再是推荐的并行调度入口。

Worker agent 上下文注入由 `parallel` 使用 map assignment packet 完成：

- 读取 `.arbor/maps/<initiative>/map.md`
- 读取 `.arbor/maps/<initiative>/map.json`
- 读取目标 `.arbor/tasks/<package>/prd.md` / `task.md` / `task.json` / `context/*.jsonl`
- 读取依赖 package summaries
- 只允许处理自己的 `.arbor/tasks/<package>/` execution boundary
- 不修改 sibling package 的 `task.json`

## 四个原语

### 🧭 Create — 创建 initiative map

触发："给 X 建 project map" / "为 X 做 domain map" / "这个大项目先画个 map" / brainstorm 判断当前需求过大。

流程：
1. 命名（kebab-case，按项目/上位主题）。
2. 读取用户显式引用的 research / package PRD；如未引用，只基于当前会话事实。
3. 生成 `.arbor/maps/<initiative>/map.md` 与 `.arbor/maps/<initiative>/map.json`：
   - `map.md` 包含 Project framing / Package graph / Execution waves / Cross-package contracts / Shared capabilities / Open blockers / Recommended next move
   - `map.json` 包含 packages、depends_on、path、prd/task/execution status、orchestration strategy
4. 使用 `create-split-packages` materialize child package stubs；只创建 `.arbor/tasks/<package>/` 和 draft PRD/template，不创建 T-xxx。
5. 运行 `map-check` 查看 ready / blocked / active / complete package。
6. 输出 map 摘要、已 materialized packages、ready/blocked 状态和推荐第一个 package-local brainstorm。
7. 如需并行推进，提示用户使用 `/sdd-kit:parallel` 或 “并行推进 <initiative>”。

### 🔄 Update — 更新 initiative map

触发："更新 map" / "把这个 package 加到 map" / "标记 X ready-for-task"。

流程：
1. 读取现有 `.arbor/maps/<initiative>/map.md` 与 `map.json`。
2. 根据新增 research / package PRD / task aggregate / execution metadata（branch/worktree/PR/owner）更新对应表格；机器状态优先通过 `arbor.py map-check` 从 child `task.json` 同步。
3. 保持 map 是当前结构视图，不记录冗长过程，也不展开 package-local T-xxx 明细。
4. 更新 `map.md` 的 `updated:`，并让 `map.json` 反映当前 package status。
5. 输出变更摘要。

### ✅ Check — 检查大项目推进状态

触发："现在大项目下一步是什么" / "检查 map" / "哪些 package blocked"。

流程：
1. 读取 `map.json`，并同步读取每个 child package 的 `task.json`。
2. 运行 `arbor.py map-check <initiative>` 计算 package graph、execution waves、dependency blockers 是否自洽。
3. 输出：ready packages、blocked packages、active packages、complete packages、当前 wave、最小下一步。
4. 不自动推进。

### 🚦 Dispatch — 交给 parallel skill

触发：用户要“并行推进”或 Trellis-like 统筹分发。

流程：
1. 不在 map skill 中直接启动 worker。
2. 提示并切换到 `/sdd-kit:parallel` / `用 parallel skill` / `并行推进 <initiative>`。
3. `parallel` 内部运行 `arbor.py map-check <initiative>`。
4. `parallel` 内部运行 `arbor.py map-plan-agents <initiative> --max-parallel <N>`。
5. `parallel` 只对 assignments 中的 ready packages 启动 autonomous package pipeline workers。
6. worker 在自己的 package boundary 内按 `task.json.next_action` 推进，直到 reviewed/completed、blocked 或 decision-needed。
7. blocked packages 不启动。

## 核心规则

1. **Map 只服务 large initiative** —— 不要给小需求增加仪式感。
2. **一个上位项目一个 map** —— map 管多个 executable task packages。
3. **Map 不写详细 PRD** —— 详细方案属于 brainstorm 的 `prd.md`。
4. **Map 不拆 T-xxx** —— package-local T-xxx 明细留在 `.arbor/tasks/<package>/task.md`。
5. **Map materialize child package stubs** —— package graph 确认后，执行 `create-split-packages`，让每个 child package 立即成为 `.arbor/tasks/<package>/`。
6. **Map 不创建 `.arbor/tasks/<initiative>/`** —— 上位 initiative 只在 `.arbor/maps/<initiative>/` 中存在。
7. **`map.json` 是统筹状态源** —— `map.md` 负责人类可读解释，ready/blocked/agent assignment 以 `map.json` + child `task.json` 为准。
8. **Package 是执行边界** —— Map 记录 package-level branch/worktree/PR/依赖；不为每个 T-xxx 建执行边界。
9. **Execution waves 表达顺序，不做无约束自动调度** —— foundation package 先做，依赖满足后再 fan-out。
10. **统筹只分配 ready package** —— 有依赖的 package 必须等待依赖 package reviewed/completed/merged 后才进入 `map-plan-agents` assignment。
11. **上下文注入是显式 packet** —— worker context 包含 map.md、map.json、目标 package 的 prd/task/task.json/context 和 dependency summaries；不让 worker 自由改 sibling package。
12. **跨域契约是一等公民** —— 大项目漂移常发生在 contract，而不是单个页面。
13. **状态要短、准、可导航** —— map 是索引，不是日志。
14. **Map 不隐式自动推进到 task/impl** —— map 的 check/update 只报告；自主推进交给显式的 `parallel` skill。
15. **Parallel 是 wave-by-wave pipeline** —— 当前 ready wave 的 worker 完成后重新 `map-check`，依赖满足再 fan-out downstream。

## 目录结构

```text
.arbor/maps/
└── <initiative>/
    ├── map.md
    ├── map.json
    └── context/
        └── agent-assignments.jsonl
.arbor/tasks/
├── <child-package-a>/   # materialized stub, prd.status=draft, package_sizing=split_applied
└── <child-package-b>/
```

## 初始化

```text
python3 plugins/sdd-kit/tools/arbor.py create-map <initiative> --title "<title>"
python3 plugins/sdd-kit/tools/arbor.py create-split-packages <initiative> \
  --package "<package>::<title>::<dep1,dep2>::<boundary reason>" \
  --actor map \
  --decision "package graph materialized from .arbor/maps/<initiative>/map.md"
python3 plugins/sdd-kit/tools/arbor.py map-check <initiative>
python3 plugins/sdd-kit/tools/arbor.py map-plan-agents <initiative> --max-parallel 2

# user-facing orchestration entry:
# /sdd-kit:parallel <initiative>
# 用 parallel skill
# 并行推进 <initiative>
```

如果 `.arbor/maps/` 不存在，首次使用时静默创建。

## 本 skill 不做的事

- 不采集 raw evidence（用 research）
- 不定稿单个 executable package PRD（用 package-local brainstorm）
- 不拆 T-xxx（用 task）
- 不写代码（用 impl）
- 不做语义审计（用 review）
- 不创建上位 initiative 的 `.arbor/tasks/<initiative>/`
- 不维护工作日志 / 会话记忆

## 何时不激活

- 用户只是在做一个清晰、单一 feature → 直接 brainstorm / task
- 用户仍在发散且连能力簇都不清楚 → 先 research
- 用户要执行某个具体 T-xxx → 用 impl
