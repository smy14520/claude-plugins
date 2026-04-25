---
name: map
description: "Maintain `.arbor/maps/<project>.md` as a lightweight domain/project map for large projects that naturally split into multiple bounded task packages. Captures domains, package PRD/task links, cross-domain contracts, shared capabilities, dependencies, blockers, and recommended next move. Does NOT replace research, does NOT write detailed PRDs, does NOT decompose tasks, and does NOT auto-advance. Invoke only on explicit user request (e.g. '用 map skill 维护 <project>')."
---

# Map — 大项目 Domain / Project Map

维护 `.arbor/maps/<project>.md`。Map 是大项目的结构导航层：当一个上位主题自然拆成多个 bounded task packages 时，用它记录当前项目如何被分域、各子域推进状态、跨域契约与推荐下一步。

```text
research → [map?] → brainstorm → task → impl → review
```

`map` 是可选层，只在 large project / 多 bounded changes 时使用。small / medium case 不需要强行创建 map。

## 定位

Map 不是 research，也不是 PRD：

- research 记录探索过程、raw evidence、notes 与 readiness。
- brainstorm 冻结一个 bounded change 的 package-local PRD/context：`.arbor/tasks/<name>/prd.md`。
- map 维护多个 bounded task packages 之间的当前结构、依赖与导航。

## 三个原语

### 🧭 Create — 创建项目地图

触发："给 X 建 project map" / "为 X 做 domain map" / "这个大项目先画个 map"。

流程：
1. 命名（kebab-case，按项目/上位主题）。
2. 读取用户显式引用的 research / task package；如未引用，只基于当前会话事实。
3. 生成 `.arbor/maps/<project>.md`，至少包含：
   - Project framing
   - Domains / bounded task packages
   - Cross-domain contracts
   - Shared capabilities
   - Dependency graph
   - Open blockers
   - Recommended next move
4. 输出摘要，不自动创建 PRD / task。

### 🔄 Update — 更新项目地图

触发："更新 map" / "把这个 package 加到 map" / "标记 X ready-for-task"。

流程：
1. 读取现有 `.arbor/maps/<project>.md`。
2. 根据新增 research / package PRD / task 状态更新对应表格。
3. 保持 map 是当前结构视图，不记录冗长过程。
4. 更新 `updated:`。
5. 输出变更摘要。

### ✅ Check — 检查大项目推进状态

触发："现在大项目下一步是什么" / "检查 map" / "哪些子域 blocked"。

流程：
1. 读取 map。
2. 检查 domains、contracts、dependency graph、blockers 是否自洽。
3. 输出：ready domains、blocked domains、最小下一步。
4. 不自动推进。

## 核心规则

1. **Map 只服务 large project** —— 不要给小需求增加仪式感。
2. **一个上位项目一个 map** —— map 管多个 bounded task packages。
3. **Map 不写详细 PRD** —— 详细方案属于 brainstorm 的 `prd.md`。
4. **Map 不拆执行任务** —— 执行冻结属于 task。
5. **跨域契约是一等公民** —— 大项目漂移常发生在 contract，而不是单个页面。
6. **状态要短、准、可导航** —— map 是索引，不是日志。
7. **不自动推进** —— 推荐下一步只是建议。

## 目录结构

```text
.arbor/maps/
└── <project>.md
```

## 初始化

如果 `.arbor/maps/` 不存在，首次使用时静默创建。

## 本 skill 不做的事

- 不采集 raw evidence（用 research）
- 不冻结单个 bounded change（用 brainstorm）
- 不拆任务（用 task）
- 不写代码（用 impl）
- 不做语义审计（用 review）
- 不维护工作日志 / 会话记忆

## 何时不激活

- 用户只是在做一个清晰、单一 feature → 直接 brainstorm / task
- 用户仍在发散且连能力簇都不清楚 → 先 research
- 用户要执行某个具体 T-xxx → 用 impl
