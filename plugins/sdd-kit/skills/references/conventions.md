# sdd-kit skill conventions

所有 sdd-kit skill 默认遵守下列约定。每个 SKILL 无需重复声明；有差异时在各自 SKILL 里覆盖。

## 语言

面向用户的 workflow 输出默认中文。代码、命令、schema 字段、`.arbor` / `.wiki` 元数据字段名按项目既有风格。

## Arbor helper

Helper 入口是裸命令 `sdd-arbor`（Claude Code 自动把插件 `bin/` 加入 PATH）。调用 Arbor helper 时，不通过 `which` / `python import` / 拼接插件根目录变量探测入口；直接用 `sdd-arbor`。

不确定参数时运行 `sdd-arbor <subcommand> --help`，以 help 输出为准。

常用命令速查见 [`arbor-helper.md`](arbor-helper.md)。

## Skill 边界（对所有 skill 生效）

- PRD（`.arbor/tasks/<package>/prd.md`）是需求 source of truth，由 brainstorm 写，其它 skill 不改。
- `task.json` 是 lifecycle source of truth，通过 `sdd-arbor` helper 读写，不手写。
- `.wiki/` 是 orientation 层，不是 source of truth；实现或 review 前验证代码和 `.arbor`。
- skill 之间不自动推进；阶段切换由用户显式触发。
- 写 `.wiki/` 必须由用户显式触发（例外：brainstorm 可引用已有 wiki 页面）。
