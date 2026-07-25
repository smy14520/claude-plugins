# seed-kit 通用约定

使用语言：中文。

## 原则

- **不确定时查证，别假设**：动手前查权威依据（文档、既有约定、代码现状、官方源），下结论前验证（跑命令、看输出）。别用记忆、习惯或单次结果代替证据。
- 五个 skill（research、brainstorm、impl、review、wiki）全部由用户主动触发，互不自动切换阶段——skill 之间不自动推进。
- `.arbor/.wiki/` 是项目记忆层：`seed wiki index --json` 看地图（有哪些页），`seed wiki collect --query "<概念>"` 按需精准拉取相关页——给地图，按需放大，不全量倾倒。收尾时按阶段职责写回（brainstorm 写 decision/module，review 写 gotcha/cross_cut），写回后 `seed wiki index --write` 刷新索引。
- `prd.md` 是需求 source of truth：slice 内联在 PRD 中（`### [ ] S-NNN 标题` heading，checkbox + prose 在一起）。进度状态 = checkbox；git log 是代码进度。没有其他状态文件。
- 分支与提交属于用户；agent 在合适的节点提示 commit。
- **标准分层（机制在插件，标准在项目）**：插件只给栈无关机制（三类验证手段、验收条目、gate、review-loop、`seed` CLI）。项目标准自管，分三处：
  - **测试纪律**（测试工具、覆盖门槛、DoD）放 `.claude/rules/`。
  - **品味、设计语言**（参考产品、配色字体、质量门槛）放 `DESIGN.md`。
  - `CLAUDE.md` 做入口。
  skill 写验收条目、写测试、对账时读它们；项目未提供标准时，插件只提供默认基准。

> PRD 验证设计（验收条目驱动 / 三类验证 / judge loop / rubric 格式 / 硬规则）见 [`verification.md`](./verification.md)——brainstorm / impl / review 读；research / wiki 不需要。

## 调用名全名登记表（别猜，照抄）

命名不对称是历史遗留，**直接照抄下列全名**，不要加/减前缀：

- **Skill**（用户主动触发，**无** `seed-` 前缀）：`seed-kit:brainstorm` / `seed-kit:impl` / `seed-kit:review` / `seed-kit:research` / `seed-kit:wiki`
- **编排命令**（slash command）：`seed-kit:review-loop` / `seed-kit:review-prd`
- **Agent**（由 skill/command 编排派发，**带** `seed-` 前缀，用户不直接调用）：`seed-kit:seed-impl` / `seed-kit:seed-review` / `seed-kit:seed-judge` / `seed-kit:seed-validator` / `seed-kit:seed-assert` / `seed-kit:seed-prd-review`

> 拿不准时回查这张表。常见错：把 skill `seed-kit:impl` 喊成 agent 名 `seed-kit:seed-impl` → Unknown skill。

## 目录

```
.arbor/tasks/<task>/      # prd.md / review.md / done-logs/ / notes/
.arbor/research/<topic>/  # index.md / raw/ / notes/
.arbor/.wiki/            # 项目知识层（导航层，非 source of truth）
```

## seed CLI

`seed` 入口：`${CLAUDE_PLUGIN_ROOT}/bin/seed`（也可 `python3 ${CLAUDE_PLUGIN_ROOT}/tools/seed.py`），在项目根目录运行。**`CLAUDE_PLUGIN_ROOT` 在 bash 子 shell 常为空**，确定性兜底：`SEED_PATH=$(command -v seed) && PLUGIN_ROOT=${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$(dirname "$SEED_PATH")")" && pwd -P)}`，再用 `$PLUGIN_ROOT/bin/seed`。

```bash
seed new <task>                                  # 脚手架任务目录 + prd.md 模板
seed status [<task>] [--json]                    # 进度 / 结构校验 / next slice
seed done <task> --slice S-NNN --test "..." [--quality "..."]  # 跑 agent 传入的测试+质量命令，全过则翻 checkbox（唯一合法入口）
seed review-mark <task> --verdict <reason> [--round N]  # 落 review-loop 终态 marker
seed score aggregate --rubric <rubric.json> \
  --score-files <file1.json> <file2.json> ... \
  --out <aggregate.json>                        # 聚合多个 score-file（多裁判模式）
seed wiki index|search|collect|lint              # .wiki/ 工具
```
