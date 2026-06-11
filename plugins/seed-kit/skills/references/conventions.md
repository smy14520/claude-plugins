# seed-kit 通用约定

使用语言：中文。

## 原则

- 五个 skill（research / brainstorm / impl / review / wiki）全部由用户主动触发，互不自动联动：不要主动去搜 research、查 wiki、推进下一阶段，除非用户明确指定。
- `prd.md` 是需求 source of truth；slice checkbox + `evidence/` 是唯一进度状态；git log 是代码进度。没有其他状态文件。
- agent 不自动 commit；在合适的节点提示用户 commit。

## 目录

```
.seed/tasks/<task>/      # prd.md / review.md / evidence/ / notes/
.seed/research/<topic>/  # index.md / raw/ / notes/
.wiki/                   # 项目知识层（导航层，非 source of truth）
```

## seed CLI

`seed` 入口：`${CLAUDE_PLUGIN_ROOT}/bin/seed`（也可 `python3 ${CLAUDE_PLUGIN_ROOT}/tools/seed.py`），在项目根目录运行。

```bash
seed new <task>                                  # 脚手架任务目录 + prd.md 模板
seed status [<task>] [--json]                    # 进度 / 证据状态 / 结构校验 / next slice
seed run-check <task> --slice S-NNN -- <命令>     # 真实执行 PRD 声明的命令，落盘证据
seed run-check <task> --slice S-NNN \
  --manual "<PRD 声明的 manual 项原文>" \
  --note "<验证了什么、结论>" --evidence "<证据指针>"
seed done <task> --slice S-NNN                   # 证据齐备后勾选 checkbox（唯一合法入口）
seed wiki index|search|collect|lint              # .wiki/ 工具
```

硬规则（由 helper 与 hook 保证，不需要靠记忆）：

- `run-check` 的命令必须与 PRD `- 验证:` 声明完全一致，不接受替代/弱化命令。
- `done` 只认落盘证据：automated 项需 passed，manual 项需 note + evidence。
- 不要手工编辑 checkbox 或 `evidence/`（会被 hook 拦截）。
