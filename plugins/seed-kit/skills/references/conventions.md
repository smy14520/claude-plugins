# seed-kit 通用约定

使用语言：中文。

## 原则

- **不确定时查证，别假设**：动手前查权威依据（文档、既有约定、代码现状、官方源），下结论前验证（跑命令、看输出）。别用记忆、习惯或单次结果代替证据。
- 九个 skill（research、brainstorm、wayfinder、impl、check、review、wiki、init、handoff）之间：进入要么用户发起，要么 agent 提议后用户同意，**绝不单方进入**；轻流转（brainstorm↔wayfinder↔research）点头即进；PRD 定稿后的独立审查（`seed-prd-review`）是 brainstorm 的默认收尾工序，自动派发不待点名；重操作（`impl` 开工、`review-loop` 深审）须用户显式点名。skill 内部动作自动推进。impl 收尾的内联自查是 impl 自己的收尾语义——编排者按 seed-kit:check 的清单执行，不 dispatch check；check 作为独立 skill 仍可单独触发。
- `.arbor/.wiki/` 是项目记忆层：`seed wiki index --json` 看地图（有哪些页），`seed wiki collect --query "<概念>"` 按需精准拉取相关页——给地图，按需放大，不全量倾倒。收尾时按阶段职责写回（brainstorm 写 decision/module，review 写 gotcha/cross_cut），写回后 `seed wiki index --write` 刷新索引。
- `prd.md` 是需求 source of truth：`## Design` 承载整体层（状态空间/跨片联动/接口契约，slice 条目引用它，轻任务显式跳过），slice 内联在 PRD 中（`### [ ] S-NNN 标题` heading，checkbox + prose 在一起）。进度状态 = checkbox；git log 是代码进度。`impl-state.json` 是任务档案（dossier）：锚点（起点 SHA，写一次锁死）+ 每 slice handoff + 证据指针——交接与续接用；`gate-attempts/` 是 gate 失败留痕（熔断计数依据）。以上都不构成第二套进度。
- 分支与提交属于用户；agent 在合适的节点提示 commit。
- **标准分层（机制在插件，标准在项目）**：插件只给栈无关机制（三类验证手段、验收条目、gate、review-loop、`seed` CLI）。项目标准自管，分三处：
  - **测试纪律**（测试工具、覆盖门槛、DoD）放 `.claude/rules/`。
  - **品味、设计语言**（参考产品、配色字体、质量门槛）放 `DESIGN.md`。
  - `CLAUDE.md` 做入口。
  skill 写验收条目、写测试、对账时读它们；项目未提供标准时，插件只提供默认基准。
- **review 环节必须做准则对照**：读项目质量标准（位置见上面「标准分层」；改动触及插件自身时含该插件的 CLAUDE.md），对照本次 diff 触及的准则逐条检查是否遵守。产出：每条准则 → 遵守/违反 → 证据（file:line + 准则原文）。实现层违反直接修；准则本身冲突或需改 → 报告用户拍板，不单方定。

> PRD 验证设计（验收条目驱动 / 三类验证 / judge loop / rubric 格式 / 硬规则）见 [`verification.md`](./verification.md)——brainstorm / impl / review 读；research / wiki 不需要。

## 调用名全名登记表（别猜，照抄）

命名不对称是历史遗留，**直接照抄下列全名**，不要加/减前缀：

- **Skill**（用户主动触发，**无** `seed-` 前缀）：`seed-kit:brainstorm` / `seed-kit:impl` / `seed-kit:check` / `seed-kit:review` / `seed-kit:research` / `seed-kit:wayfinder` / `seed-kit:wiki` / `seed-kit:init` / `seed-kit:handoff`
- **编排命令**（slash command）：`seed-kit:review-loop` / `seed-kit:review-prd`
- **Agent**（由 skill/command 编排派发，**带** `seed-` 前缀，用户不直接调用）：`seed-kit:seed-impl` / `seed-kit:seed-review` / `seed-kit:seed-judge` / `seed-kit:seed-validator` / `seed-kit:seed-assert` / `seed-kit:seed-prd-review` / `seed-kit:seed-prototype`

> 拿不准时回查这张表。常见错：把 skill `seed-kit:impl` 喊成 agent 名 `seed-kit:seed-impl` → Unknown skill。

## 目录

```
.arbor/tasks/<task>/
├── prd.md           # 进度 source of truth：Design 整体层 + slice 内联（### [ ] S-NNN heading + prose）
├── review.md        # review 追加记录
├── done-logs/       # seed done 机械验证记录
├── review-loop.json # 显式 task 级 review-loop 终态（可选）
├── impl-state.json  # 任务档案：锚点（起点 SHA）+ slice handoff + 证据指针（可选；非进度）
├── gate-attempts/   # seed done 失败留痕（熔断计数依据）
└── notes/           # impl 过程备注（可选）

.arbor/research/<topic>/  # index.md / raw/ / notes/
.arbor/maps/<slug>/       # wayfinder 决策图：map.md + tickets/ 决策票（决策账本，非进度，图清即冻结）
.arbor/prototypes/<slug>/ # seed-prototype 一次性原型（弃置产物，不进交付）
.arbor/.wiki/             # 项目知识层（导航层，非 source of truth）
```

## seed CLI

`seed` 在项目根目录运行。定位插件根（templates/ 等资源）用 `seed root`——不依赖 `CLAUDE_PLUGIN_ROOT`（bash 子 shell 常为空），不手写 readlink 兜底。

```bash
seed new <task>                                  # 脚手架任务目录 + prd.md 模板
seed root                                          # 打印插件根目录（定位 templates/ 等资源）
seed status [<task>] [--json]                    # 进度 / 结构校验 / next slice / gate 失败计数与熔断 / 锚点与档案存在性
seed done <task> --slice S-NNN --test "..." [--quality "..."]  # 跑 agent 传入的测试+质量命令，全过则翻 checkbox（唯一合法入口）
seed review-mark <task> --verdict <reason> [--round N] [--depth inline|single|full]  # 落终态 marker（inline=编排者内联自查 / single=派过 1 个 review agent / full=5 agent review-loop）
seed impl-state init|reset-attempts <task>  # 任务档案：锚点（起点 SHA 写一次锁死）/ 单 slice 目标 / 熔断清零
seed handoff add <task> --slice S-NNN --note "…" # 追加 slice handoff（隐性事实）到档案
seed score aggregate --rubric <rubric.json> \
  --score-files <file1.json> <file2.json> ... \
  --out <aggregate.json>                        # 聚合多个 score-file（多裁判模式）
seed wiki index|search|collect|lint              # .wiki/ 工具
seed map new <slug>                              # 脚手架 .arbor/maps/<slug>/（map.md + tickets/）
seed map status <slug> [--json]                  # 决策图状态：open/closed 计数 + frontier 推导（只读）
```
