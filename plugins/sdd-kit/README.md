# sdd-kit

**SDD Kit** — Brainstorm-Driven Delivery + Deterministic Task Packages + Persistent Wiki Knowledge Layer

新一代 SDD 工具包。基于对 [autolearn-sdd-kit](../autolearn-sdd-kit) 的反思、[Karpathy LLM-Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) 的持久化知识模式、[superpowers](https://github.com/obra/superpowers) 的 skill-first 路线、[Trellis](https://github.com/mindfold-ai/Trellis) 的 task package / context 思路构建。

## 设计原则

1. **少即是多**：上下文精而少，不追求"完整覆盖"
2. **可控优先**：阶段之间无强制跳转，由用户显式决定
3. **可拆解优先**：第二阶段产物首先服务于 task 拆解，而不是追求 contract 炫技
4. **来源可追溯**：关键判断、场景、风险要能回到 research / 本地文件 / 外部 URL
5. **知识复利**：跨需求可复用的资产沉淀到 wiki
6. **机械事务脚本化**：AI 负责判断、归纳、拆解；`sdd-arbor` 负责创建目录、维护 `task.json`、追加 JSONL、校验结构

## 核心流程

```text
research? → brainstorm
              ├─ small: .arbor/tasks/<package>/prd.md → task → impl → review
              └─ large: clarified framing → map → child package → task → impl → review
                                                                  ↑
                                                                  └─ 用户主动 ingest → wiki（持久）
```

`map` 是大项目可选统筹层：当一个上位主题自然拆成多个 executable task packages 时，用 `.arbor/maps/<initiative>/map.md` 维护人类可读的 package graph、execution waves、跨 package 契约、依赖和下一步导航，用 `.arbor/maps/<initiative>/map.json` 维护机器可读状态，并立即 materialize child package stubs：`.arbor/tasks/<package>/`。small / medium case 不需要强行创建 map。

每阶段独立可用，文档之间**无强制跳转**。

可选：sdd-kit 不内置 parallel runtime，但用户可以在任意阶段显式要求 Claude Code 使用 Agent Team 作为会话层协作能力。说“用 Team Auto”时，当前会话会先给出 2-4 个阵型选项（如辩论会、双推、Shadow Review、Review Panel）并推荐一个，由用户选择后再启动；用户明确授权时才直接开 Team。详见 [AGENT_TEAM.md](./AGENT_TEAM.md)。

- `research` 负责发散与澄清。
- `brainstorm` 必须先完成需求澄清与整体 design framing：小需求形成 single executable package PRD，大需求在业务范围和 implementation framing 都清楚后，才输出 clarified initiative framing 并交给 `map`。
- `map` 负责大项目 package graph / execution waves / contracts / blocker navigation，并 materialize child package stubs；它不是执行器，不自动派发实现。
- `task` 负责 secondary sizing guard、执行冻结与 T-xxx 拆解。
- `impl` 负责消费 task-local context 交付代码。
- `review` 负责独立语义审计。

`[[wikilink]]` 仅作为可选导航线索。

| 阶段 | 职责 | 产物位置 |
|------|------|---------|
| research | index-first 的需求探索工作区：发散、提问、收集资料、带来源地解释事实、逐步收敛理解，并通过 `index.md` 对外提供统一入口 | `.arbor/research/<topic>/` |
| map | 大项目统筹层：`map.md` 维护 executable packages、execution waves、跨 package 契约、依赖与导航；`map.json` 维护机器可读 dependency/status；并 materialize child package stubs | `.arbor/maps/<initiative>/map.md` + `.arbor/maps/<initiative>/map.json` + `.arbor/tasks/<package>/` stubs |
| brainstorm | 需求澄清 + design framing：小需求写 single package PRD；大需求在业务与 implementation framing 都清楚后，只输出 clarified initiative framing / map handoff，不创建 child stubs | `.arbor/tasks/<package>/prd.md` 或 clarified framing / map handoff |
| task | Secondary sizing guard + 执行冻结 + package-local T-xxx 拆解：只处理 `fits_package` / `split_applied` 的 executable package | `.arbor/tasks/<package>/task.md` + `task.json` + `context/*.jsonl` |
| impl | 按 task 执行代码实现 + 运行自己的 acceptance（SelfCheck） | 代码本身 + `.arbor/tasks/<package>/task.json` |
| review | 对照 PRD + task + diff + wiki 做独立语义审计（4 态: APPROVED / APPROVED_WITH_NOTES / NEEDS_REWORK / BRAINSTORM_DRIFT） | `.arbor/tasks/<package>/review.md` |

**Task lifecycle 约定**：`task.json` 是 task package 的唯一生命周期状态源；`prd.md` 是 executable package PRD/context artifact；`task.md` 是稳定任务定义，impl/review 不修改；需求做错后的修正默认是 forward-only amendment：PRD 追加 `AMD-xxx`，task 追加新的 T-xxx，旧定义不静默改写；`review.md` 是追加式语义审计日志，不作为当前状态源；large initiative 的统筹状态由 `.arbor/maps/<initiative>/map.json` 聚合 child `task.json`；`status.md` 已废弃，新的 task package 不得创建。

**Execution boundary 约定**：

- `.arbor/tasks/<package>/` 表示 executable package boundary，可记录轻量 branch / PR metadata，但不暗示自动派发执行。
- Large initiative 属于 `.arbor/maps/<initiative>/`，不要创建 `.arbor/tasks/<initiative>/`。
- Brainstorm 先完成 clarified initiative framing。
- Map 确认 package graph 后，应立即 materialize child package stubs：`.arbor/tasks/<package>/`，并记录 `package_sizing=split_applied`。
- `T-xxx` 是 package-local control / acceptance / dependency / review 单元，不是默认 branch / PR 单元；如果某个 T-xxx 需要独立交付边界，应拆成新的 package 并由 map 维护依赖。
- Brainstorm/map 必须先完成 package boundary sizing：brainstorm 负责 single package 的 `fits_package`，map 负责 split 后 child package 的 `split_applied`；task 只验证 sizing 状态并阻止 `unchecked` / `split_recommended` 进入 T-xxx。
- 下游实现只依赖明确完成事实：上游 package `completed`、execution `merged` 或 PR `merged`；`reviewed` alone 不解锁下游实现。跨 package 缺口走 contract request，不能直接修改 sibling internals。

**为什么 impl 和 review 分开？** impl 严格只看 task-local context，无法可靠地做语义审计（会污染 "translator" 角色）。review 在新上下文里独立读 PRD + `git diff` + wiki，才能真正交叉验证。详见 [skills/review/SKILL.md](./skills/review/SKILL.md)。

## Deterministic task package

新产物统一写入：

```text
.arbor/tasks/
└── <package>/
    ├── prd.md              # brainstorm skill 创建/维护
    ├── task.md             # task skill 创建/维护，稳定任务定义
    ├── task.json           # lifecycle source of truth，sdd-arbor 机械维护
    ├── review.md           # review 追加日志
    └── context/
        ├── impl.jsonl      # implementation context packets
        ├── review.jsonl    # review context packets
        └── sources.jsonl   # machine-readable source index
```

`sdd-arbor` 是 plugin `bin/` 暴露的轻量 deterministic state layer。它会从已安装插件位置定位 `tools/arbor.py`，但命令仍在当前业务项目 cwd 中读写 `.arbor` / `.wiki`：

```text
sdd-arbor create <package> --mode strict-atomic --title "<title>"
sdd-arbor create-map <initiative> --title "<title>"
sdd-arbor set-package-sizing <package> --status fits_package --actor brainstorm --phase brainstorm --decision "这是一个可用的 package 边界"
sdd-arbor create-split-packages <initiative> --package "<package>::<title>::<dep1,dep2>::<中文 boundary reason>" --actor map --decision "package graph 已从 .arbor/maps/<initiative>/map.md materialize"
sdd-arbor map-check <initiative>
sdd-arbor record-contract-request <initiative> --consumer <package-b> --producer <package-a> --request "需要 producer 提供的稳定 contract" --status open --json
sdd-arbor set-package-sizing <package> --status split_applied --actor map --phase map --decision "package 已从 .arbor/maps/<initiative>/map.md 拆出"
sdd-arbor set-prd-status <package> --status ready-for-task --actor brainstorm --note "PRD 已就绪"
sdd-arbor add-amendment <package> --title "退款规则修正" --wrong "退款行为缺失" --correct "全额退款撤销权限" --affects-task T-003 --actor brainstorm
sdd-arbor add-child <package> --id T-001 --title "ADD ..." --milestone M-01 --role shared --ready true
sdd-arbor add-context <package> --type impl --task T-001 --kind constraint --summary "中文上下文摘要"
sdd-arbor add-context-batch <package> --type impl --entry-json '{"task_id":"T-001","kind":"constraint","summary":"中文上下文摘要"}'
sdd-arbor freeze-definition <package> --actor task --note "task definition 已冻结"
sdd-arbor module-summary <package> --initiative <initiative> --json
sdd-arbor wiki-index --json
sdd-arbor wiki-search "balance refund" --json
sdd-arbor wiki-collect --query "balance refund" --limit 5 --json
sdd-arbor validate <package>
sdd-arbor show <package>
```

脚本只做机械事务：创建目录、初始化模板、维护状态、追加 JSONL、校验 schema、记录 package-level execution metadata、聚合 map ready/blocked/active/complete/missing 状态，以及维护 contract request。它不判断需求范围、不写 PRD、不拆任务语义、不决定 review 是否通过、不创建 branch/PR、不启动 agent，也不会把 `task.json.tasks[]` 自动同步进 `task.md`；task skill 必须写实 Markdown 任务定义。

可选 hook guardrail：`plugins/sdd-kit/hooks/arbor_guard.py` 可作为 PreToolUse 脚本，阻止直接写 `.arbor` control state、直接写 context JSONL 和明显 destructive bash。Hook 只守底线，语义判断仍在 skill/review/helper。

## 需求修正 / Amendment

如果已经拆过 task 或开始 impl/review 后发现需求不对，不回滚旧 PRD/task，直接告诉 brainstorm 追加 amendment：

```text
/sdd-kit:brainstorm .arbor/tasks/course-order-entitlement
T-003 的退款规则不对：全额退款要撤销权限，部分退款不撤销。请追加为 amendment。
```

后续流程：`brainstorm` 追加 `AMD-xxx` → `task` 追加新 T-xxx（带 `source_amendment/corrects`）→ `impl` 实现增量 → `review` 验证增量与回归。

## Brainstorm 定位

`sdd-kit` 现在将第二阶段正式命名为 `brainstorm`：

- 它不是 project-level 长期规范层
- 它必须先做需求澄清与整体 design framing，需求不明确时不能拆包
- `ready-for-brainstorm` research 不等于 `ready-for-map`；business scope 清楚但技术栈、项目形态、repo baseline、数据/测试策略等 implementation framing 缺失时，brainstorm 继续提问
- 它采用 context first、一次一个高价值问题、具体选项与权衡的对话式收敛方式
- 小需求可写入 single executable package PRD：`.arbor/tasks/<package>/prd.md`
- 大需求在业务与 implementation framing 都清楚后，只输出 clarified initiative framing / map handoff；`.arbor/maps/<initiative>/` 与 child package stubs 由 `map` 创建
- 它首先服务于 `task` 的直接拆解，而不是追求“看起来很严谨”的 contract 模板

Legacy note：旧 `.arbor/brainstorms/<package>.md` 只作为 fallback input。新流程不再创建该路径。

## Wiki 持久化层

```text
.wiki/
├── index.md          # 轻量入口，不是全量目录
├── log.md            # 可选追加式操作日志
├── Modules/
│   └── <Module Title>.md
├── Decisions/
├── Concepts/
├── Gotchas/
└── Sources/
```

**核心约定**：
- `.wiki/` 是 project-local orientation/index layer，不是 `.arbor` source of truth。
- 每页 frontmatter 至少包含 `title`、`description`、`tags`、`type`、`summary`。
- 完成稳定 milestone 后，可用 `sdd-arbor module-summary <package> --json` 产出 packet，再由 wiki skill/subagent 写/更新 `.wiki/Modules/<Title>.md`。
- Module note 不写 line numbers；定位用 file path + stable symbol / route / table / config / test / contract id。
- 检索先用 `wiki-index/search/collect` 输出 JSON，再选择性读取页面；用于实现或 review 时必须验证当前代码和 `.arbor`。

详见 [skills/wiki/SKILL.md](./skills/wiki/SKILL.md)。

## 当前状态

- [x] wiki skill（project-local `.wiki` + module summary publish + index/search/collect）
- [x] research skill（index-first 工作区 + raw 证据层 + notes 主题笔记 + log 时间线 + 可多轮续写）
- [x] map skill（大项目 package graph + execution waves + cross-package contracts + serial readiness navigation）
- [x] brainstorm skill（需求澄清 / design framing + single package PRD / map handoff + 来源追踪）
- [x] task skill（secondary sizing guard + 执行冻结 + milestone / child task + DAG + helper-written context）
- [x] impl skill（四态状态机 + 可验证 acceptance + task-local context + 不静默决策）
- [x] review skill（独立语义审计 + 4 态 + 读 PRD/task/diff/wiki + 不改代码）
- [x] deterministic helper（`sdd-arbor`：create / validate / map-check / context / wiki retrieval / lifecycle state）

## 使用

**skills-only 结构**。每个 skill 是 `skills/<skill-name>/SKILL.md`，无 `commands/` 中间层（plugin skill 本身就会被 Claude Code 注册为可直接调用的入口——多一层 commands 壳等于自己读自己，冗余且容易因相对路径产生 bug）。

触发方式:

```text
自然语言（显式点名，推荐）:
  "用 research skill 调研 <topic>"
  "用 map skill 维护 <project>"
  "用 brainstorm skill 收敛 <package>"       # 未指定模式时先选 normal / grill
  "用 brainstorm grill-me 压力测试 <plan>"   # grill 模式逐问追压并给推荐答案
  "用 task skill 拆 <package>"
  "用 impl skill 执行 <package> 的 T-001"
  "用 review skill 审计 <package> 的 T-001"
  "用 wiki skill ingest / query / lint <content>"
  "这个 impl 用 Team Auto，先给我几个阵型选项"
  "这个 review 开多 agent，从架构、测试、代码质量和项目公约角度审"

slash command（由 Claude Code 从 SKILL.md 的 name 字段自动注册）:
  /sdd-kit:research
  /sdd-kit:map
  /sdd-kit:brainstorm
  /sdd-kit:task
  /sdd-kit:impl
  /sdd-kit:review
  /sdd-kit:wiki
```

`map-check` 只给出 large initiative 的串行下一步和 blocker；如果要推进实现，直接调用 `/sdd-kit:brainstorm` / `/sdd-kit:task` / `/sdd-kit:impl` / `/sdd-kit:review` 处理对应 package。

阶段之间**不自动跳转**。wiki 也必须显式触发。

> **防止过度触发靠什么？** **description 写严**。plugin skill 的 `disable-model-invocation` 字段 [是无效的](https://github.com/anthropics/claude-code/issues/22345)（Claude Code 已知 bug，flag 对 plugin skill 被忽略）。所有 skill 的 description 都明确写了 "Invoke only on explicit user request (e.g. '用 X skill ...')"，由模型根据描述自我约束。这是 superpowers 等成熟 plugin 的现行做法。

**`.arbor/` 是 sdd-kit / Arbor 的确定性状态目录**：research、map、task package 写入这里。**`.wiki/` 是项目本地知识导航层**，用于 module note 和可检索摘要，不作为状态源。`.claude/` 只作为 Claude Code 的配置/命令/集成目录，不再承载工作流产物。

## 和 autolearn-sdd-kit 的差异

| 维度 | autolearn-sdd-kit | sdd-kit |
|------|-------------------|---------|
| 阶段数 | 8（brainstorm/research/design/spec/tasks/impl/review/extract-experience） | 5 核心阶段 + 1 个大项目可选 map 层（research/map/brainstorm/task/impl/review） |
| 命令层 | 14 厚 commands（每个做 orchestration，重复 skill 内容） | 0 commands — 纯 skills-only；plugin runtime 自动把 SKILL.md 的 name 注册为 `/sdd-kit:<skill-name>` |
| 第二阶段产物 | design/spec 并存，边界较重 | `brainstorm`：先做需求澄清 / design framing；小需求产出 executable package PRD，大需求交给 map 拆包 |
| 触发方式 | 自然语言 + 命令并存（隐式触发开放） | 显式自然语言"用 X skill …" 或 `/sdd-kit:<skill-name>` |
| Agent | 9 agents | 无内置固定 agent；实现与审计由用户显式进入对应 skill，review 仍建议在独立上下文里跑 |
| 知识组织 | 4 抽屉（experience / modules / rules / gotchas）+ 3 索引 | `.arbor/` 确定性状态 + `.wiki/` 项目本地导航层 + map + task package |
| 阶段跳转 | 文档互引较重 | 文档无强制引用；阶段显式推进；map 只在大项目中作为导航 |
| 知识检索 | 向量检索思路（ContextDetective） | `.wiki` frontmatter + wikilinks + deterministic `wiki-index/search/collect` JSON，module note 不写行号 |
| 语义审计 | review phase 存在但和 impl 边界模糊 | review 独立 skill，读 PRD + diff + wiki，4 态（APPROVED / APPROVED_WITH_NOTES / NEEDS_REWORK / BRAINSTORM_DRIFT） |
| impl 自验证 | verify 和 execute 混同 | impl 只做 SelfCheck（跑自己的 acceptance），语义审计归 review |
| 状态维护 | 主要靠文档 | `task.json` + `sdd-arbor` 维护 deterministic lifecycle |
