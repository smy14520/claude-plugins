---
name: map
description: "Maintain `.arbor/maps/<initiative>/` as the canonical coordination layer for large initiatives that split into executable task packages. Materializes child package stubs, maintains map.md/map.json, records dependencies/contracts/blockers, and checks serial ready/blocked/active/complete/missing package state. Does NOT create T-xxx, dispatch execution, or replace package-local PRDs. Invoke only on explicit user request."
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
- `.arbor/tasks/<package>/`：map 中确认的 executable child package stub。

Map 不写详细 package PRD，不拆 T-xxx，不写代码，不审计。Package-local PRD 由 brainstorm 负责，T-xxx 由 task 负责。

`.arbor/` 是控制面：只保存 map、PRD、task、review、context 和状态。产品源码/测试必须写到 repo 的实际实现目录，不能写到 `.arbor/tasks/<package>/`。

**禁止**为上位 initiative 创建 `.arbor/tasks/<initiative>/`。

## 串行统筹边界

- Map 负责结构和状态视图，不负责执行调度。
- `map-check` 只输出可推进 package、阻塞原因和完成状态。
- 需要真正推进时，由用户或当前会话显式进入对应 child package 的 `brainstorm` / `task` / `impl` / `review`。
- 下游实现只依赖明确完成事实：上游 package `completed`、execution `merged` 或 PR `merged`；`reviewed` alone 不解锁下游实现。

## 原语

### Create — 创建 initiative map

触发：brainstorm 已输出 clarified initiative framing，或用户明确要求为已经清楚的大需求建 map。

流程：

1. 命名 initiative（kebab-case）。
2. 读取 brainstorm framing、research notes、当前 repo 上下文和用户补充，确认需求与 implementation framing 已经清楚到可以拆 package graph。
3. 写清为什么需要多个 executable packages；若仍缺少会影响拆包的整体选择（例如项目形态、技术栈、前后端关系、repo baseline、数据/权限/测试策略），先回 brainstorm/user 澄清，不创建 child stubs。
4. 用 arbor helper 创建/更新 initiative map（`create-map`；参数以 `--help` 为准）。
5. 在 `map.md` 中写：当前 framing / implementation framing / package graph / execution waves / cross-package contracts / blockers / next orchestration check。
6. 在 `map.json` 中维护 packages、depends_on、path、prd/task/execution status、orchestration strategy 和 contracts。
7. `summary` / `reason` / `boundary_reason` 等给人读的值默认写中文；字段名、enum、路径、命令和协议标签保持英文。
8. 记录 dependency gate：下游只在上游明确完成或 merged 后推进实现。
9. 记录 cross-package contracts；consumer 缺 producer 能力时追加 contract request，不让 consumer patch producer internals。
10. 用 arbor helper materialize child package stubs（`create-split-packages`；Map 是唯一负责该动作的阶段）。
11. 运行 `map-check`，输出 ready / blocked / active / complete / missing。
12. 如需执行，提示用户按 `map-check` 输出显式进入对应 package 的 `brainstorm` / `task` / `impl` / `review`。

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

输出：ready / blocked / active / complete / missing、当前 wave、最小下一步。不自动推进。

## 核心原则

1. Map 只服务 large initiative；小需求不要加仪式感。
2. 一个上位项目一个 map。
3. Map 不写详细 PRD，不拆 T-xxx。
4. Package graph 确认后 child package stub 应立即存在。
5. `map.json` 是统筹状态源；`map.md` 是人类解释层。
6. Package 是需求/评审/回滚边界；branch/PR metadata 只是可选记录，不代表自动执行。
7. Execution waves 表达顺序；依赖满足后再推进下游。
8. 跨域 contract 是一等公民；缺口用 contract request，而不是互改 sibling internals。
9. Downstream implementation 只依赖 completed/merged；reviewed alone 不等于 mainline fact。
10. Map 不隐式推进到 task/impl。

## 目录结构

```text
.arbor/maps/<initiative>/
├── map.md
└── map.json

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
- 不启动执行者或自动推进 child package。
