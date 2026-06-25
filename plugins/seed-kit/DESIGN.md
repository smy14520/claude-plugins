# seed-kit 设计文档

seed-kit 是 上一代工作流 的轻量继任者：取其精华（PRD source of truth、真实验证证据、wiki 导航层），去其糟粕（多层状态机、24 个命令、为已删除特性残留的 schema）。

## 动机

上一代工作流 多轮迭代暴露的弊病：

- 命令面 24 个（arbor 20 + wiki 4），其中 `set-execution` / `set-pr` / `repair-context` 等几乎无人调用；AI 在过宽的命令面前选择困难。
- 状态机叠床架屋：顶层 6 态 + 9 个 legacy 映射 + impl 4 态 + review 4 态 + slice 3 态 + check 4 态 + execution 7 态 + PR 6 态。execution / PR / sizing 字段来自已删除的 team-auto / 拆包时代，永远为空但 schema 还在。
- 文档漂移与墓碑代码：README 残留旧概念，`package_children.py` 整个文件只剩 raise。

外部调研（spec-kit / Kiro / Trellis / Ralph loop / OpenSpec / Anthropic harness 研究）收敛出的不变量：

> **PRD 是需求的 source of truth，文件系统是状态的 source of truth，git 是进度的 source of truth，机器可验证的 gate 是正确性的 source of truth。**
> 在这四个锚点之上，流程越轻、命令越少、阶段越不强制，存活率越高。

第四条只敢说"正确性"，不敢说"质量"——这是刻意的。质量分两半，本性相反，要用相反的工具：

- **可验证的一半**（余额算对、422、契约、转账不计收支）：能写出可证伪的 check，二值 gate（exit 0 / verdict=pass）正合适，约束越紧越好。
- **不可验证的一半**（好不好用、顺不顺手、好不好看、优不优雅）：写不出能由命令直接断言的 check——这就是 Goodhart。二值功能 gate 用在这里不是"不够"，而是**有害**：它在通过线以上没有提升动力，把一条本无天花板的质量轴**封顶在最小可过**；而"按 spec 通过"又把模型从生成模式切到合规模式。二者叠加，产出一个能过测试却没法真实使用的"半成品"。

所以这一半不能交给 exit code 或插件内置审美，只能靠**测试当地板（保持绿、不回归）+ 一个感知真实产物、按项目 rubric 打分的独立 judge 在环**。这一环的"评判"本质上无法由 helper 机械化；但评判结果的结构、artifact 和 score/bar 通过关系可以由 helper 机械 gate。承认它、把它做顺，比假装 exit code 能替代它更稳。

**Gate 边界**：gate 管**正确性为主**；但项目用 rubric 显式声明的 judge scoring 也按门槛进 gate（opt-in，声明即 gate）。未声明的体验质量仍不压 gate（靠 review / 人判断，质量没有上限）。

被反复证明失败的设计恰好是 上一代工作流 的病灶：过重状态机（"reinvented waterfall"）、过多命令的 context tax、依赖模型自觉的口头约束、大体量生成文档。

## 设计原则

1. **五个 skill 全部由用户主动触发，互不自动耦合。** 不存在"brainstorm 自动去搜 research"、"impl 自动查 wiki"这种隐式链路；需要时用户一句话指定（"去读 research/xxx"、"看 wiki 里导出的注意事项"）。
2. **纯 Markdown 状态，没有状态机。** `prd.md` 的 slice checkbox + git log 就是全部进度；断点续作 = 读 prd.md + git log。没有 task.json，没有 set-status。
3. **helper 只做确定性的状态 / 证据读写。** 脚手架、解析校验、执行验证命令并落盘 exit_code / 输出、记录 judge / human 证据、勾选 checkbox——全是确定性动作，不调用 LLM、不做语义判断。其中 `seed done` 是唯一的硬 gate。
4. **命令面极小：核心 4 个（new / status / run-check / done）+ wiki 家族。** 命令少到 AI 不需要选择。
5. **hook 只守两条底线：** 拦截破坏性命令；拦截绕过 gate 手工勾选 checkbox / 手写 evidence。
6. **用户拥有 commit。** agent 不自动 commit；slice 完成后提示用户 commit 时机，进度锚点是 checkbox + evidence，不是 commit。

## 五个 skill

### research — 给需求收集外部资料

职责：把一个需求的外部世界整理成 AI 可读的资料。竞品调研（哪家测评网站做得好、好在哪、数据源和字段有哪些）、外部 API 摸底（小红书客服接口、接入流程）都属于这里。

- 工作区：`.arbor/research/<topic>/`，index-first：`index.md`（导航与结论）+ `raw/`（原始抓取）+ `notes/`（整理后的可读笔记）。
- 不做设计决策、不写 PRD；产出是"资料已足够支撑后续讨论"。
- 只在用户显式要求时触发。

### brainstorm — 需求收敛访谈

职责：把模糊想法收敛成可执行的 PRD。从零的项目（"我想做个 Steam 模拟游戏"）引导用户做技术选型、玩法、2D/3D 等关键决策；已有项目（"加小红书 AI 客服"）先读代码理解现状再提问边界与接入方式。

- 交互循环：一次只问一个高价值问题，每个问题给出推荐答案和理由；能从代码确认的事实先自行查证，不问用户。
- 用户可主动指定读 `.arbor/research/<topic>/` 或 `.wiki/`；skill 不主动搜索。
- 终点：`seed new <task>` 脚手架 + 写入 `prd.md`（需求、可证伪 AC、轻量 Technical Framing、ordered Slices）。
- PRD 后续可以直接修改；改动在 prd.md 底部"变更记录"留一行即可，不设 amendment 编号仪式。

### impl — 执行 PRD

职责：按 `## Slices` 顺序执行，一次一个 slice，代码就是进度。

- 入场：`seed status <task>` 看哪些 slice 未完成（断点续作入口），从第一个未勾选的继续。
- 每个 slice：实现 → `seed run-check` 真实执行该 slice 声明的验证命令 → `seed done` 勾选（gate 见下）→ 提示用户 commit。
- 并行编排是用户主动选项，不是内建阶段：用户说"前后端并行 / 开 team"时用 Agent Team（worker 实现 + lead 只协调审查，按 slice 设 gate）；默认单会话连续执行。
- 卡住协议显式化：缺上下文 → 在 prd.md 变更记录写明缺口，停下来问用户；不允许悄悄缩小 scope。

### review — 语义审计

职责：用户主动触发，读 PRD + diff + evidence，逐条 AC 对账，产出追加式 `review.md`。

- 独立性：review 在不携带 impl 过程上下文的新会话 / 新 agent 中进行（生成者 ≠ 验证者）。
- 形态灵活：可以单 agent，也可以用户要求时开 Agent Team 多角度审计（正确性 / 安全 / 性能各一个视角）。
- 不改代码、不改需求；结论只有文字记录，没有状态流转——需要返工就是用户安排下一轮 impl。

### wiki — 项目知识层

职责：承载项目与 AI 一同成长的知识。两类内容：research 中沉淀下来值得长期保留的资料（用户说"把这个收录进 wiki"）；项目链路知识（"加导出要在 4-5 个文件里加枚举"这类多文件链路，记下来以后一句"看 wiki 里导出的注意事项"就能复用）。

- `.wiki/` 是导航层，不是 source of truth；定位后必须验证当前代码。
- 灵活性靠自由的 area 轴：游戏 / web / 软件项目各自长出自己的 area 划分，type 保持小的封闭集（如 guide / link-map / reference）。
- 操作：ingest（收录）、update（代码变了之后刷新某页）、`seed wiki index / search / collect / lint`。
- 只在用户显式要求时触发；lint 检查断链与陈旧标记。

## Artifact 结构

```
.arbor/
├── tasks/<task>/
│   ├── prd.md        # 需求 + AC + ## Slices（有序 checkbox 索引）= 唯一状态
│   ├── slices/       # S-NNN.md：每个 slice 的验收与验证项（内容唯一的家）
│   ├── review.md     # review 追加记录
│   ├── evidence/     # run-check 落盘：S-NNN/<seq>-<kind>.json + .log
│   └── notes/        # impl 过程备注（可选）
└── research/<topic>/
    ├── index.md      # 导航与结论
    ├── raw/          # 原始资料
    └── notes/        # 整理后的笔记
.wiki/                # 项目知识层（独立于 .arbor，跟项目走）
```

### prd.md 与 slice 文件骨架

单一归属，防止大需求膨胀 prd.md，也防止 上一代工作流 时代"同一事实两个家"的同步漂移：**顺序与状态记录在 prd.md 索引，验收与验证记录在 slice 文件**，没有任何内容写两遍。共享上下文（背景 / AC / Framing）留在 prd.md——它是每个 slice 都需要的，拆到哪都得读；按 task 再拆只会制造互相引用。impl 的阅读模型：通读 prd.md（薄）建立整体理解，干活时只读当前 slice 文件。

```markdown
# <标题>                            # prd.md

## 背景与目标
## 需求与验收标准
<!-- 每条 AC 可证伪：Given/When/Then，至少覆盖一条失败路径 -->
## Technical Framing
<!-- 轻量：选型、边界、不做什么 -->
## Slices
### [ ] S-001 <标题>
<!-- 只放索引行；内容在 slices/S-NNN.md，标题须一致（seed status 校验） -->
## 变更记录
<!-- 一行一条：日期 + 改了什么 + 为什么 -->
```

```markdown
# S-001 <标题>                      # slices/S-001.md

## 交付面
- backend-domain
- web-ui

## 验收
<!-- 对应哪几条 AC；必要时展开 GWT 细节与失败路径 -->
## 验证面
- [assert][backend-domain] domain-ledger-平衡: 借贷必平，非法余额断言失败
- [judge][web-ui] ui-journey: 浏览器 UI 旅程，按本文件 rubric 裁决
```

## helper 命令面（共 4 个 + wiki 家族）

| 命令 | 做什么 |
|---|---|
| `seed new <task>` | 脚手架 `.arbor/tasks/<task>/`（prd.md + slices/S-001.md 模板） |
| `seed status [<task>]` | 解析 prd.md 索引与 slices/，输出 slice 进度 / evidence 摘要 / 下一个未完成 slice，并机械校验索引行 ↔ slice 文件一致、交付面是否被验证面覆盖（断点续作与编排的唯一入口） |
| `seed run-check <task> --slice S-NNN --obligation <id> -- <cmd>` | [assert] 真实执行命令，绑定到 obligation，落盘 exit_code + 输出 |
| `seed run-check <task> --slice S-NNN --obligation <id> --verdict pass\|fail --trace "..." --artifact "..."` | [judge] legacy 二值裁决（pass 必须 artifact） |
| `seed run-check <task> --slice S-NNN --obligation <id> --rubric <rubric.json> --score-file <score.json> --trace "..." --artifact "..."` | [judge] scoring gate：helper 读取项目 rubric 与裁判 score-file，计算 verdict |
| `seed run-check <task> --slice S-NNN --obligation <id> --note "..." [--by "..."]` | [human] 记录人工签收 |
| `seed done <task> --slice S-NNN` | gate：该 slice 文件声明的全部验证项都有 passed / 已记录证据，且结构校验通过 → 由 helper 勾选索引 checkbox；否则拒绝并列出缺口 |
| `seed wiki index / search / collect / lint` | 沿用 wiki（已是零依赖独立模块） |

没有 set-status、没有 record-impl-result、没有 record-review、没有 amendment 命令、没有内部隐藏命令。

## 防 AI 偷懒方案（分层）

1. **写需求时就写预期证据**（brainstorm 层）：每条 AC 可证伪（GWT + 失败路径），每个 slice 声明交付面并把验证项写成验收义务 `[kind][surface] <obligation-id>: <可观测行为>`——一条义务对应一个可证伪维度，不要用一条套件命令覆盖多个维度。验收标准含糊是偷懒的第一入口。
2. **硬 gate，但有诚实的边界**（helper 层）：`seed status` 机械检查交付面是否被验证面覆盖；`seed done` 只认 `seed run-check` 落盘的证据——assert 需 exit 0、judge 需 verdict=pass（legacy 手写或 scoring gate 计算）、human 需签收记录；不存在 not_run / 默认跳过。**但 gate 只保证 evidence 形状与结果达标，不保证语义正确**：一条命令可能测试写假，评分也可能误判。所以语义可信度由交付面结构约束 + 三类验证词汇 + 烟雾嗅探 + 独立 judge + artifact + review 共同把住，而不是单压在 exit code 或分数上。
3. **hook 守底线**（hook 层）：拦截直接把 prd.md 的 `[ ]` 改成 `[x]`、手写 `evidence/`、破坏性命令（`rm -rf`、`git reset --hard`）。
4. **生成者 ≠ 验证者**（review 层）：review 用干净上下文逐 AC 对账 diff，专查偷懒签名——弱化的断言、吞掉的异常、新增 `@ts-ignore` / `eslint-disable`、抄实现的假测试、悄悄收窄的 scope、**验证降级 / 交付面冒充**（可 assert 的写成 judge / human、后端测试冒充 web-ui / e2e、裸 curl 烟雾、judge 自评）。review 同时是 `[judge]` 项的独立裁判。
5. **小步 + 代码即进度**（流程层）：一次一个 slice，slice 完成即提示用户 commit；上下文污染时随时可以开新会话从 `seed status` 续作，不依赖会话记忆。

第 2、3 层是机械的（脚本保证），第 1、4、5 层是流程约定（skill 描述方向，不堆禁令）。

### 两种失败模式：蒙混 vs 诚实地最小满足

上面五层主要防的是**蒙混**——弱化断言、假测试、交付面冒充、judge 自评。这类是廉价偷懒，可以机械化堵死（第 2、3 层做得好）。

还有第二种失败，更隐蔽：**agent 完全诚实，只是精确地做了"刚好过 gate 的最小实现"**。功能全对、测试全绿，成品却没法用（典型：UI 是能用但粗糙的半成品，文案是占位，CLI 手感粗糙）。它不是 bug，是"把不可验证质量塞进二值 gate"的设计产物（见动机里那条公理的拆分）——施动者越诚实越会这样，因为它在如实优化你给的目标。

蒙混能靠机制治；诚实地最小满足不能，要换范式：

- **测试是地板，不是完成定义。** impl 的目标是"在地板保持绿的前提下做到可交付品质"，不是"把测试跑绿就停"。`seed done` 代表声明义务已过 gate；若声明了 scoring judge，也代表该义务达到项目 rubric，但不代表未声明维度或整体品味没有上限。
- **不可验证质量靠"judge 在环"，且 judge 必须看真实产物。** 评判本身不由 helper 机械化；helper 只校验独立 judge 的 artifact、rubric/score-file 形状，并按项目门槛计算 verdict。评分维度、bar、参考来自项目，插件不内置审美。
- **用参考注入品味，不用插件清单。** 参考产品 / 设计语言 / "感觉像 X" 传递的是丰富先验，把 agent 从"品味的发明者"降为"翻译者"；这些标准写进项目 PRD / DESIGN / rules，不写死在 seed-kit。

外部佐证（Anthropic harness 的 generator/evaluator 视觉闭环、Eval-Driven Development 的"测试当地板而非天花板"、对齐研究"不可验证目标需要 process oversight + 判断在环"、社区共识"地基严格 + 工艺自由"）都收敛到同一处：**正确性用断言 gate，体验质量用项目 rubric + 独立 judge scoring gate + artifact。**

## 交付面（自由）+ 三类验证（kind 封闭）

验证项是验收义务：`[kind][surface] <obligation-id>: <可观测行为>`。`surface` 表示覆盖哪个交付面（参考词汇表 backend-domain / api / web-ui / e2e / compliance / infra，项目可扩展；helper 只校验"声明面被覆盖"，面名字无关、不按面名规定 kind），`kind` 表示谁判定它对，obligation 是可证伪的可观测行为（命令不写在 slice，由 run-check `--obligation <id>` 绑定）。这样避免把所有验证压成同一种形状，也避免“后端测试冒充整条 Web 产品交付”。

- **assert** — 命令本身就是会失败的断言（测试套件 / 契约回放 / Playwright spec）。gate = exit 0。有状态 API 流写成**自包含**集成测试（内部 setup→act→assert），而不是跨命令、靠 shell 变量串状态的 curl（seed 的 run-check 每次 check 是独立 subprocess，shell 变量不跨 check）。
- **judge** — 难以机械断言的语义 / UI / 手感，由独立上下文的裁判（生成者≠验证者，详见 verification）按项目 rubric 裁决。gate = verdict=pass；verdict 可由 legacy `--verdict` 给出，也可由 helper 根据 `--rubric + --score-file` 计算。judge 必须裁**真实产物**（截图 / 实时页面 / 实际输出），不是裁代码；helper 只校验 artifact 存在和评分证据形状，不调用 LLM、不解释品味。
- **human** — 真人 stakeholder 签收，限 compliance 等本质不可自动化交付面。gate = 签收记录。

原则：assert 优先，能用 judge 就不要叠加 human；human 覆盖可断言交付面是设计气味，但 helper 不机械禁止，由项目规则与 review 查验证降级。一个 slice 只能 `[human][compliance]` 验证是设计气味。外部调研（Playwright MCP + Test Agents、Pact/WireMock 契约与录制回放、LLM-as-a-Judge、spec-kit 的 [NEEDS CLARIFICATION]）都指向同一个分层：**能机械断言的先机械断言，到不了顶的才上独立裁判，裁判也覆盖不了的才上人**。

## 从 上一代工作流 的取舍清单

**带走**：run-check 真实执行 + 证据落盘；PRD 含 Technical Framing + ordered Slices 的结构；brainstorm 访谈循环（一次一问 + 推荐答案）；research index-first 工作区；wiki 四命令与"导航层非 source of truth"定位；arbor_guard 的破坏性命令拦截。

**丢弃**：六态 lifecycle + 全部 legacy 映射；impl / review 的四态 enum 与 record-* 命令；task.json 及其全部 schema（execution / PR / sizing / agents / checkpoints）；amendment 编号仪式；marker 覆盖对账的复杂规则（由"逐 slice 证据 gate + review 对账"替代）；doctor 独立 skill（并入 `seed status` 与 `seed wiki lint`）；内部隐藏命令；scenario_eval 重型框架（新 kit 用轻量单测起步）。

## 实施路线

- **M1 骨架**：`tools/seed.py`（new / status / run-check / done）+ 单测；`.claude-plugin/plugin.json`；prd.md 模板。
- **M2 skills**：brainstorm / impl 两个 SKILL.md（先打通"收敛 → 执行 → 证据"主链路），guard hook。
- **M3 外环**：research / review / wiki 三个 SKILL.md；wiki 代码迁移（或直接复用）。
- **M4 实战校验**：拿一个真实小需求跑全链路，按失败模式"立路牌"式补约束，而不是预先堆规则。

每个 milestone 完成即可用，不需要等全部建完。
