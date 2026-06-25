# seed-kit 通用约定

使用语言：中文。

## 原则

- **不确定时查证，别假设**：动手前查权威依据（文档、既有约定、代码现状、官方源），下结论前验证（跑命令、看输出）。别用记忆、习惯或单次结果代替证据。
- 五个 skill（research、brainstorm、impl、review、wiki）全部由用户主动触发，互不自动联动：不要主动去搜 research、查 wiki、推进下一阶段，除非用户明确指定。
- `prd.md` 是需求 source of truth：`## Slices` 是有序 checkbox 索引（顺序与状态唯一的家）；每个 slice 的验收与验证项写在 `slices/S-NNN.md`（内容唯一的家）。进度状态 = 索引 checkbox + `evidence/`；git log 是代码进度。没有其他状态文件。
- agent 不自动 commit；在合适的节点提示用户 commit。
- **标准分层（机制在插件，标准在项目）**：插件只给栈无关机制（三类验证、交付面自由标签、覆盖规则、烟雾嗅探、`seed` CLI）。项目标准自管，分三处：
  - **测试纪律**（测试工具、UI 是否要求交互断言、覆盖门槛、DoD）放 `.claude/rules/`（如 `testing.md`，可用 `paths:` frontmatter 只在相关文件加载）。
  - **品味、设计语言**（参考产品、配色字体、质量门槛）放 `DESIGN.md`。
  - `CLAUDE.md` 做入口与 `@import` 引用。
  skill 设验证面、写测试、对账时读它们；项目未提供标准时，插件只提供通用地板（反半成品）。

> PRD 验证设计（交付面 / 三类验证 / judge loop / rubric 格式 / helper 硬规则）见 [`verification.md`](./verification.md)——brainstorm / impl / review 读；research / wiki 不需要。

## 调用名全名登记表（别猜，照抄）

命名不对称是历史遗留，**直接照抄下列全名**，不要加/减前缀：

- **Skill**（用户主动触发，**无** `seed-` 前缀）：`seed-kit:brainstorm` / `seed-kit:impl` / `seed-kit:review` / `seed-kit:research` / `seed-kit:wiki`
- **编排命令**（slash command）：`seed-kit:review-loop` / `seed-kit:review-prd`
- **Agent**（review-loop 内部编排派发，**带** `seed-` 前缀，用户/模型不直接调用）：`seed-kit:seed-impl` / `seed-kit:seed-review` / `seed-kit:seed-judge` / `seed-kit:seed-validator` / `seed-kit:seed-assert`

> 拿不准时回查这张表。常见错：把 skill `seed-kit:impl` 喊成 agent 名 `seed-kit:seed-impl` → Unknown skill。

## 目录

```
.arbor/tasks/<task>/      # prd.md / slices/ / review.md / evidence/ / notes/
.arbor/research/<topic>/  # index.md / raw/ / notes/
.wiki/                   # 项目知识层（导航层，非 source of truth）
```

## seed CLI

`seed` 入口：`${CLAUDE_PLUGIN_ROOT}/bin/seed`（也可 `python3 ${CLAUDE_PLUGIN_ROOT}/tools/seed.py`），在项目根目录运行。**`CLAUDE_PLUGIN_ROOT` 在 bash 子 shell 常为空**，确定性兜底：`PLUGIN_ROOT=${CLAUDE_PLUGIN_ROOT:-$(dirname $(dirname $(readlink -f $(command -v seed))))}`，再用 `$PLUGIN_ROOT/bin/seed`。

```bash
seed new <task>                                  # 脚手架任务目录 + prd.md / slices/S-001.md 模板
seed status [<task>] [--json]                    # 进度 / 证据状态 / 结构校验 / 烟雾标记 / next slice
seed run-check <task> --slice S-NNN --obligation <id> -- <命令>   # [assert] 真实执行，绑定到 obligation，落盘 exit_code + 输出
seed run-check <task> --slice S-NNN \
  --obligation <id> --verdict pass|fail \
  --trace "<裁决依据/证据指针>" \
  --artifact "<看过的截图/输出>" \
  [--grade "..." --by "<裁决者>"]   # [judge] legacy 二值裁决
seed run-check <task> --slice S-NNN \
  --obligation <id> --rubric <rubric.json> --score-file <score.json> \
  --trace "<评分依据>" --artifact "<看过的截图/输出>" \
  [--by "<裁决者>"]   # [judge] scoring gate，helper 计算 verdict
seed run-check <task> --slice S-NNN \
  --obligation <id> --rubric <rubric.json> --aggregation-file <aggregate.json> \
  --trace "<评分依据>" --artifact "<看过的截图/输出>" \
  [--by "<裁决者>"]   # [judge] 多裁判聚合模式，verdict 由 helper 计算
seed score aggregate --rubric <rubric.json> --score-files <file1.json> <file2.json> ... --out <aggregate.json>   # 聚合多个 score-file（多裁判模式）
seed run-check <task> --slice S-NNN \
  --obligation <id> --note "<验证了什么、结论>" [--by "<签收人>" --evidence "<证据指针>"]   # [human]
seed done <task> --slice S-NNN                   # 证据齐备后勾选 checkbox（唯一合法入口）
seed wiki index|search|collect|lint              # .wiki/ 工具
```
