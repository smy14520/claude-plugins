# sdd-kit

**SDD Kit** — Brainstorm-Driven Delivery + Deterministic Task Packages + Persistent Wiki Knowledge Layer

新一代 SDD 工具包。基于对 [autolearn-sdd-kit](../autolearn-sdd-kit) 的反思、[Karpathy LLM-Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) 的持久化知识模式、[superpowers](https://github.com/obra/superpowers) 的 skill-first 路线、[Trellis](https://github.com/mindfold-ai/Trellis) 的 task package / context 思路构建。

## 设计原则

1. **少即是多**：上下文精而少，不追求"完整覆盖"
2. **可控优先**：阶段之间无强制跳转，由用户显式决定
3. **可拆解优先**：第二阶段产物首先服务于 task 拆解，而不是追求 contract 炫技
4. **来源可追溯**：关键判断、场景、风险要能回到 research / 本地文件 / 外部 URL
5. **知识复利**：跨需求可复用的资产沉淀到 wiki
6. **机械事务脚本化**：AI 负责判断、归纳、拆解；`tools/arbor.py` 负责创建目录、维护 `task.json`、追加 JSONL、校验结构

## 核心流程

```text
research → map? → brainstorm → task → impl → review
            │                            ↑
            └─ parallel? ────────────────┘
   ↖             │         │      │        │
   │             │         │      │        └─ 独立审计（读 prd + task package + diff + wiki）
   │             │         │      └─ 自运行 acceptance（机械自检，不做语义审计）
   │             │         └─ task package：prd.md / task.md / task.json / review.md / context/*.jsonl
   └─────────────┴─────────┴──────┴────────┴──→ 用户主动 ingest → wiki（持久）
```

`map` 是大项目可选统筹层：当一个上位主题自然拆成多个 executable task packages 时，用 `.arbor/maps/<initiative>/map.md` 维护人类可读的 package graph、execution waves、跨 package 契约、依赖和下一步导航，用 `.arbor/maps/<initiative>/map.json` 维护机器可读状态，并立即 materialize child package stubs：`.arbor/tasks/<package>/`。small / medium case 不需要强行创建 map。

每阶段独立可用，文档之间**无强制跳转**。`research` 负责发散与澄清；`map` 负责大项目 package graph / execution waves，并 materialize child package stubs；`parallel` 是 Trellis-like 一等统筹入口，自动选择 ready packages、注入 context、分发 package dispatch workers，并自主推进 brainstorm/task/impl/review 直到 reviewed、blocked 或 decision-needed；`brainstorm` 负责先做 boundary routing，再把 executable package 收敛为 PRD/context artifact；`task` 负责 secondary sizing guard、执行冻结与 T-xxx 拆解；`impl` 负责消费 task-local context 交付代码；`review` 负责独立语义审计。`[[wikilink]]` 仅作为可选导航线索。

| 阶段 | 职责 | 产物位置 |
|------|------|---------|
| research | index-first 的需求探索工作区：发散、提问、收集资料、带来源地解释事实、逐步收敛理解，并通过 `index.md` 对外提供统一入口 | `.arbor/research/<topic>/` |
| map | 大项目统筹层：`map.md` 维护 executable packages、execution waves、跨 package 契约与导航；`map.json` 维护机器可读 dependency/status/agent assignment context；并 materialize child package stubs | `.arbor/maps/<initiative>/map.md` + `.arbor/maps/<initiative>/map.json` + `.arbor/tasks/<package>/` stubs |
| brainstorm | Boundary routing + executable package PRD/context：单 package 则写 `.arbor/tasks/<package>/prd.md`，large initiative 则路由到 map 并创建 child package stubs | `.arbor/tasks/<package>/prd.md` 或 `.arbor/maps/<initiative>/map.md` |
| parallel | Trellis-like 一等统筹入口：自动 map-check、生成 ready package assignment/context、分发最多 N 个 package dispatch worker，并在 package boundary 内自主推进 brainstorm/task/impl/review；blocked/decision-needed 回报用户 | `.arbor/maps/<initiative>/context/agent-assignments.jsonl` + worker agent sessions |
| task | Secondary sizing guard + 执行冻结 + package-local T-xxx 拆解：只处理 `fits_package` / `split_applied` 的 executable package | `.arbor/tasks/<package>/task.md` + `task.json` + `context/*.jsonl` |
| impl | 按 task 执行代码实现 + 运行自己的 acceptance（SelfCheck） | 代码本身 + `.arbor/tasks/<package>/task.json` |
| review | 对照 PRD + task + diff + wiki 做独立语义审计（4 态: APPROVED / APPROVED_WITH_NOTES / NEEDS_REWORK / BRAINSTORM_DRIFT） | `.arbor/tasks/<package>/review.md` |

**Task lifecycle 约定**：`task.json` 是 task package 的唯一生命周期状态源；`prd.md` 是 executable package PRD/context artifact；`task.md` 是稳定任务定义，impl/review 不修改；`review.md` 是追加式语义审计日志，不作为当前状态源；large initiative 的统筹状态由 `.arbor/maps/<initiative>/map.json` 聚合 child `task.json`；`status.md` 已废弃，新的 task package 不得创建。

**Execution boundary 约定**：`.arbor/tasks/<package>/` 只表示 executable package execution boundary，可记录一个 branch、一个 worktree、一个 PR 和显式 agent validation metadata。Large initiative 属于 `.arbor/maps/<initiative>/`，不要创建 `.arbor/tasks/<initiative>/`；map/brainstorm 确认 package graph 后，应立即 materialize child package stubs：`.arbor/tasks/<package>/`，并记录 `package_sizing=split_applied`。`T-xxx` 是 package-local control / acceptance / dependency / review 单元，不是默认 branch/worktree/PR 单元；如果某个 T-xxx 需要独立 PR，应拆成新的 package 并由 map 维护依赖。Brainstorm/map 必须先完成 package boundary sizing；task 只验证 sizing 状态并阻止 `unchecked` / `split_recommended` 进入 T-xxx。`parallel` skill 是用户级一等入口，内部执行 `map-check` / `map-plan-agents`，只把依赖已 reviewed/completed/merged 的 package 标为 ready 并分发 package dispatch worker；worker 在自己的 package boundary 内按 `task.json.next_action` 自主推进，遇到不确定、越界、阻塞或外部副作用时回报用户。

**为什么 impl 和 review 分开？** impl 严格只看 task-local context，无法可靠地做语义审计（会污染 "translator" 角色）。review 在新上下文里独立读 PRD + `git diff` + wiki，才能真正交叉验证。详见 [skills/review/SKILL.md](./skills/review/SKILL.md)。

## Deterministic task package

新产物统一写入：

```text
.arbor/tasks/
└── <package>/
    ├── prd.md              # brainstorm skill 创建/维护
    ├── task.md             # task skill 创建/维护，稳定任务定义
    ├── task.json           # lifecycle source of truth，tools/arbor.py 机械维护
    ├── review.md           # review 追加日志
    └── context/
        ├── impl.jsonl      # implementation context packets
        ├── review.jsonl    # review context packets
        └── sources.jsonl   # machine-readable source index
```

`tools/arbor.py` 是轻量 deterministic state layer：

```text
python3 plugins/sdd-kit/tools/arbor.py create <package> --mode strict-atomic --title "<title>"
python3 plugins/sdd-kit/tools/arbor.py create-map <initiative> --title "<title>"
python3 plugins/sdd-kit/tools/arbor.py set-package-sizing <package> --status fits_package --actor brainstorm --phase brainstorm --decision "single executable package boundary is valid"
python3 plugins/sdd-kit/tools/arbor.py create-split-packages <initiative> --package "<package>::<title>::<dep1,dep2>::<boundary reason>" --actor map --decision "package graph materialized from .arbor/maps/<initiative>/map.md"
python3 plugins/sdd-kit/tools/arbor.py map-check <initiative>
python3 plugins/sdd-kit/tools/arbor.py map-plan-agents <initiative> --max-parallel 2
python3 plugins/sdd-kit/tools/arbor.py set-package-sizing <package> --status split_applied --actor brainstorm --phase brainstorm --decision "package extracted from .arbor/maps/<initiative>/map.md"
python3 plugins/sdd-kit/tools/arbor.py set-prd-status <package> --status ready-for-task --actor brainstorm --note "prd ready"
python3 plugins/sdd-kit/tools/arbor.py add-child <package> --id T-001 --title "ADD ..." --milestone M-01 --role shared --ready true
python3 plugins/sdd-kit/tools/arbor.py add-context <package> --type impl --task T-001 --kind constraint --summary "..."
python3 plugins/sdd-kit/tools/arbor.py freeze-definition <package> --actor task --note "task definition frozen"
python3 plugins/sdd-kit/tools/arbor.py claim-package <package> --owner <actor> --branch arbor/<package> --worktree <path>
python3 plugins/sdd-kit/tools/arbor.py record-agent <package> --role review --agent <agent-name> --status passed --summary "..."
python3 plugins/sdd-kit/tools/arbor.py validate <package>
python3 plugins/sdd-kit/tools/arbor.py show <package>
```

脚本只做机械事务：创建目录、初始化模板、维护状态、追加 JSONL、校验 schema、记录 package-level execution metadata、聚合 map ready/blocked 状态、生成 autonomous package pipeline 的 agent assignment/context packet。它不判断需求范围、不写 PRD、不拆任务语义、不决定 review 是否通过、不创建 worktree/branch/PR、不启动 agent，也不会把 `task.json.tasks[]` 自动同步进 `task.md`；task skill 必须写实 Markdown 任务定义。

## Brainstorm 定位

`sdd-kit` 现在将第二阶段正式命名为 `brainstorm`：

- 它不是 project-level 长期规范层
- 它先做 boundary routing：single executable package vs large initiative/map
- 它是**单次 executable package 的 PRD/context artifact**
- 它首先服务于 `task` 的直接拆解，而不是追求“看起来很严谨”的 contract 模板
- 新写入位置是 `.arbor/tasks/<package>/prd.md`；large initiative 写入 `.arbor/maps/<initiative>/map.md` + `map.json` 并 materialize child package stubs

Legacy note：旧 `.arbor/brainstorms/<package>.md` 只作为 fallback input。新流程不再创建该路径。

## Wiki 持久化层

```text
.arbor/wiki/
├── index.md          # 全局索引（只列 root + 跨域 + 孤立 + source）
├── log.md            # 追加式操作日志
├── <root-topic>.md   # root 页面：领域入口，带 tags: [root]
├── <topic>.md        # 子页面：主题即文件名，无类型前缀
└── source-<name>.md  # 原始资料摘要（唯一带前缀的）
```

**核心约定**：
- 文件名 = 主题名，不加类型前缀
- 类型（entity / concept / gotcha / decision / moc / source）在 frontmatter
- 子页面不入 index.md，由 root 页面承担领域导航
- 关联靠 `[[wikilinks]]` 涌现，不建 MOC 层

详见 [skills/wiki/SKILL.md](./skills/wiki/SKILL.md)。

## 当前状态

- [x] wiki skill（知识层宪法 + R1-R5 维护规则含 stale-by-age 新鲜度）
- [x] research skill（index-first 工作区 + raw 证据层 + notes 主题笔记 + log 时间线 + 可多轮续写）
- [x] map skill（大项目 package graph + execution waves + cross-package contracts）
- [x] parallel skill（Trellis-like 一等统筹入口 + autonomous package pipeline + context injection packet）
- [x] brainstorm skill（boundary routing + executable package PRD/context artifact + 来源追踪）
- [x] task skill（secondary sizing guard + 执行冻结 + milestone / child task + DAG + context JSONL / sources）
- [x] impl skill（四态状态机 + 可验证 acceptance + task-local context + 不静默决策）
- [x] review skill（独立语义审计 + 4 态 + 读 PRD/task/diff/wiki + 不改代码）
- [x] deterministic helper（`tools/arbor.py`：create / validate / set-prd-status / freeze-definition / add-child / add-context / set-status / set-phase / list / show）

## 使用

**skills-only 结构**。每个 skill 是 `skills/<skill-name>/SKILL.md`，无 `commands/` 中间层（plugin skill 本身就会被 Claude Code 注册为可直接调用的入口——多一层 commands 壳等于自己读自己，冗余且容易因相对路径产生 bug）。

触发方式:

```text
自然语言（显式点名，推荐）:
  "用 research skill 调研 <topic>"
  "用 map skill 维护 <project>"
  "用 parallel skill"                 # 自动选择唯一 map，check + plan + autonomous package pipeline
  "并行推进 <initiative>"              # 指定 initiative，默认并行度 2，自主推进 ready packages
  "用 brainstorm skill 收敛 <package>"
  "用 task skill 拆 <package>"
  "用 impl skill 执行 <package> 的 T-001"
  "用 review skill 审计 <package> 的 T-001"
  "用 wiki skill ingest / query / lint <content>"

slash command（由 Claude Code 从 SKILL.md 的 name 字段自动注册）:
  /sdd-kit:research
  /sdd-kit:map
  /sdd-kit:parallel
  /sdd-kit:brainstorm
  /sdd-kit:task
  /sdd-kit:impl
  /sdd-kit:review
  /sdd-kit:wiki
```

`parallel` 是 Trellis-like 一等入口；用户不需要每次手写 `map-check` / `map-plan-agents`，也不需要通过 `map --parallel` 间接触发。执行 `/sdd-kit:parallel` 表示授权它自主推进 ready package；如果要人工审计每个阶段，直接调用 `/sdd-kit:brainstorm` / `/sdd-kit:task` / `/sdd-kit:impl` / `/sdd-kit:review`。插件 skill 的 slash command 是命名空间形式 `/sdd-kit:parallel`；裸 `/parallel` 只有在运行时额外提供别名时才成立。

阶段之间**不自动跳转**。wiki 也必须显式触发。

> **防止过度触发靠什么？** **description 写严**。plugin skill 的 `disable-model-invocation` 字段 [是无效的](https://github.com/anthropics/claude-code/issues/22345)（Claude Code 已知 bug，flag 对 plugin skill 被忽略）。所有 skill 的 description 都明确写了 "Invoke only on explicit user request (e.g. '用 X skill ...')"，由模型根据描述自我约束。这是 superpowers 等成熟 plugin 的现行做法。

**`.arbor/` 是 sdd-kit / Arbor 的项目产物目录**：research、map、task package、wiki 都写入这里。`.claude/` 只作为 Claude Code 的配置/命令/集成目录，不再承载工作流产物。

## 和 autolearn-sdd-kit 的差异

| 维度 | autolearn-sdd-kit | sdd-kit |
|------|-------------------|---------|
| 阶段数 | 8（brainstorm/research/design/spec/tasks/impl/review/extract-experience） | 5 核心阶段 + 1 个大项目可选 map 层 + 1 个可选 parallel 统筹入口（research/map/parallel/brainstorm/task/impl/review） |
| 命令层 | 14 厚 commands（每个做 orchestration，重复 skill 内容） | 0 commands — 纯 skills-only；plugin runtime 自动把 SKILL.md 的 name 注册为 `/sdd-kit:<skill-name>` |
| 第二阶段产物 | design/spec 并存，边界较重 | `brainstorm`：先做 boundary routing，再产出 executable package PRD/context artifact |
| 触发方式 | 自然语言 + 命令并存（隐式触发开放） | 显式自然语言"用 X skill …" 或 `/sdd-kit:<skill-name>` |
| Agent | 9 agents | 无内置固定 agent；`parallel` 按 ready package 启动 package dispatch workers，worker 在 package boundary 内推进 pipeline；package 可记录 branch/worktree/PR/agent validation metadata，review 仍建议在 subagent / 新会话里跑 |
| 知识组织 | 4 抽屉（experience / modules / rules / gotchas）+ 3 索引 | `.arbor/` 项目产物目录 + wiki + map + task package |
| 阶段跳转 | 文档互引较重 | 文档无强制引用；阶段显式推进；map 只在大项目中作为导航 |
| 知识检索 | 向量检索思路（ContextDetective） | Karpathy 显式导航（index → root → 子页）+ R5 新鲜度提示 |
| 语义审计 | review phase 存在但和 impl 边界模糊 | review 独立 skill，读 PRD + diff + wiki，4 态（APPROVED / APPROVED_WITH_NOTES / NEEDS_REWORK / BRAINSTORM_DRIFT） |
| impl 自验证 | verify 和 execute 混同 | impl 只做 SelfCheck（跑自己的 acceptance），语义审计归 review |
| 状态维护 | 主要靠文档 | `task.json` + `tools/arbor.py` 维护 deterministic lifecycle |
