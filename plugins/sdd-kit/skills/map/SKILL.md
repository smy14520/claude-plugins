---
name: map
description: "Maintain `.arbor/maps/<initiative>/` as the canonical coordination layer for large initiatives that split into executable task packages. Materializes child package stubs, maintains map.md/map.json, records map-time parallel_policy, and checks execution_ready/prep_ready/blocked package state; dynamic dispatch is the separate `parallel` skill. Does NOT create T-xxx or replace package-local PRDs. Invoke only on explicit user request."
---

# Map — Large Initiative / Package Graph

Map 是 large initiative 的导航和状态层。它维护多个 executable packages 之间的结构、依赖、execution waves 和 cross-package contracts。

```text
research? → brainstorm → [map] → package-local brainstorm → task → impl → review
                              ↑                              │
                              └── package status / blocker 回写到 map.json
```

## 职责边界

- `.arbor/maps/<initiative>/map.md`：人类可读导航、package graph、execution waves、contracts、blockers，以及 Brainstorm 已确认的必要 implementation framing。
- `.arbor/maps/<initiative>/map.json`：机器可读 package graph / dependency / status / orchestration state。
- `.arbor/maps/<initiative>/context/agent-assignments.jsonl`：`parallel` 的 assignment/context log。
- `.arbor/tasks/<package>/`：map 中确认的 executable child package stub。

Map 不写详细 package PRD，不拆 T-xxx，不写代码，不审计。Package-local PRD 由 brainstorm 负责，T-xxx 由 task 负责。

`.arbor/` 是控制面：只保存 map、PRD、task、review、context 和状态。产品源码/测试必须写到 repo 的实际实现目录，不能写到 `.arbor/tasks/<package>/`。

**禁止**为上位 initiative 创建 `.arbor/tasks/<initiative>/`。

## 和 parallel 的分工

- Map 负责结构和状态视图。
- `parallel` 负责主会话 lead 的 Agent Team worker pool 执行。

用户要并行推进时使用：

```text
/sdd-kit:parallel <initiative>
用 parallel skill
并行推进 <initiative>
```

`parallel` 会内部执行 `parallel-schedule`，由主会话作为 lead 创建 runtime Agent Team，并在 serial critical-path、parallel execution、parallel prep、serial integration lane 间动态切换；worker 先通过 EnterWorktree + WORKTREE_READY gate 进入 package worktree；`integration_ready` 只启动一个 serial integration worker。Map 同时维护四个并行边界：`modification_scope` 写权限、contract inputs/outputs/requests、只依赖 lead/mainline checkpoint 的主干边界、以及 `lead_serial` 串行 integration lane。主会话 lead 只协调、审查和 checkpoint，不直接实现 package/product diff。

## 原语

### Create — 创建 initiative map

触发：brainstorm 已输出 clarified initiative framing，或用户明确要求为已经清楚的大需求建 map。

流程：

1. 命名 initiative（kebab-case）。
2. 读取 brainstorm framing、research notes、当前 repo 上下文和用户补充，确认需求与 implementation framing 已经清楚到可以拆 package graph。
3. 写清为什么需要多个 executable packages；若仍缺少会影响拆包的整体选择（例如项目形态、技术栈、前后端关系、repo baseline、数据/权限/测试策略），先回 brainstorm/user 澄清，不创建 child stubs。
4. 用 arbor helper 创建/更新 initiative map（`create-map`；参数以 `--help` 为准）。
5. 在 `map.md` 中写：当前 framing / implementation framing / package graph / execution waves / cross-package contracts / blockers / next orchestration check。
6. 在 `map.json` 中维护 packages、depends_on、path、prd/task/execution status、orchestration strategy，以及每个 package 的 `parallel_policy` / `modification_scope` / contracts。
7. `summary` / `reason` / `boundary_reason` / `parallel_policy.reason` 等给人读的值默认写中文；字段名、enum（如 `independent`、`lead_serial`）、路径、命令和协议标签保持英文。
8. 对每个 package 判断并记录并行策略：
   - `independent`：不依赖 sibling，可推进到 review。
   - `contract_dependent`：依赖未完成时可先 brainstorm/task，但 impl/review 要等 dependency gate。
   - `hard_dependent`：依赖未完成前不应准备或执行。
9. 记录写权限边界：owned paths、shared/integration-sensitive paths；shared center files、global wiring、DI、routes、migrations、E2E、repo-wide config 应交给 `lead_serial` integration package 的 serial integration worker 串行处理，由主会话 lead 审查/checkpoint。
10. 记录 cross-package contracts；consumer 缺 producer 能力时追加 contract request，不让 consumer patch producer internals。
11. 用 arbor helper materialize child package stubs（`create-split-packages`；Map 是唯一负责该动作的阶段）。
12. 运行 `map-check`，输出 execution_ready / prep_ready / integration_ready / blocked / active / complete / missing。
13. 如需执行，提示 `/sdd-kit:parallel <initiative>`。

### Update — 更新 map

触发：新增 package、dependency、contract、blocker、execution metadata，或 child package 状态变化。

流程：

1. 读取 `map.md` + `map.json`。
2. 用 child `task.json` 作为 package status source。
3. 更新 map 表格和 `updated:`。
4. 保持 map 是结构视图，不展开 package-local T-xxx 明细。
5. 输出变更摘要。

### Check — 检查推进状态

触发：用户问“现在下一步是什么 / 哪些 package blocked”。

运行 arbor helper 的 `map-check`。

输出：execution_ready / prep_ready / integration_ready / blocked / active / complete / missing、当前 wave、最小下一步。不自动推进。

### Dispatch — 交给 parallel

Map skill 不直接启动 worker。用户要“并行推进”时，切换到 `parallel`：

```text
/sdd-kit:parallel <initiative>
```

## 核心原则

1. Map 只服务 large initiative；小需求不要加仪式感。
2. 一个上位项目一个 map。
3. Map 不写详细 PRD，不拆 T-xxx。
4. Package graph 确认后 child package stub 应立即存在。
5. `map.json` 是统筹状态源；`map.md` 是人类解释层。
6. Package 是执行边界；branch/worktree/PR/agent metadata 属于 `.arbor/tasks/<package>/`。
7. Execution waves 表达顺序；基线/共享能力先合并，依赖满足后 fan-out。
8. Map-time `parallel_policy` 是并行判断；不要等 parallel skill 再猜是否独立。
9. 跨域 contract 是一等公民；缺口用 contract request，而不是互改 sibling internals。
10. `modification_scope` 是并行写权限边界；shared/global integration 用 `lead_serial` 串行 lane，实际实现由 serial integration worker 做，主会话 lead 不下场写实现。
11. Downstream implementation 只依赖 completed/merged/lead checkpoint；reviewed alone 不等于 mainline fact。
12. Map 不隐式推进到 task/impl；Agent Team 自主推进交给显式 `parallel`。

## 目录结构

```text
.arbor/maps/<initiative>/
├── map.md
├── map.json
└── context/
    └── agent-assignments.jsonl

.arbor/tasks/<child-package>/
├── prd.md       # draft stub, package-local brainstorm later fills it
├── task.md      # template until task skill runs
└── task.json    # source_type=map-split, package_sizing=split_applied
```

## 本 skill 不做

- 不采集 raw evidence（research）。
- 不定稿 child package PRD（brainstorm）。
- 不拆 T-xxx（task）。
- 不写代码（impl）。
- 不做语义审计（review）。
- 不启动 autonomous workers（parallel）。
