# seed-kit

轻量 PRD-first 工作流。五个 skill 全部由用户主动触发、互不自动耦合；状态就是 `prd.md` 的 slice checkbox + `evidence/` 证据文件，没有状态机、没有 task.json。

设计动机与取舍见 [`DESIGN.md`](DESIGN.md)。

## 五个 skill

| skill | 职责 | 产出 |
|---|---|---|
| research | 给需求收集外部资料（竞品、API、数据源） | `.seed/research/<topic>/`（index.md / raw/ / notes/） |
| brainstorm | 访谈式收敛需求：一次一问 + 推荐答案 | `.seed/tasks/<task>/prd.md`（可证伪 AC + 有序 Slices） |
| impl | 逐 slice 执行 PRD，证据齐备才能勾选完成 | 代码 + `evidence/` |
| review | 干净视角逐 AC 对账 diff，专查偷懒签名 | 追加 `review.md` |
| wiki | 项目知识层：长期资料 + 多文件链路知识 | `.wiki/` 页面 |

skill 之间没有自动流转：brainstorm 不会自己去搜 research，impl 不会自己查 wiki，review 由用户主动触发。

## 状态模型

```
.seed/tasks/<task>/
├── prd.md        # 需求 source of truth；## Slices = 有序 checkbox 索引（唯一进度状态）
├── slices/       # S-NNN.md：每个 slice 的验收与验证项（内容唯一的家）
├── review.md     # review 追加记录
├── evidence/     # seed run-check 落盘：S-NNN/<seq>-<kind>.json + .log
└── notes/        # impl 过程备注（可选）
```

单一归属：顺序与状态住在 prd.md 索引，slice 内容住在 `slices/S-NNN.md`，没有任何事实写两遍；`seed status` 机械校验索引行 ↔ slice 文件一致。断点续作 = `seed status <task>` + git log。代码就是进度。

## seed CLI（核心 4 个命令 + wiki 家族）

```bash
seed new <task>                                  # 脚手架任务目录 + prd.md / slices/S-001.md 模板
seed status [<task>] [--json]                    # 进度 / 证据状态 / 结构校验 / 烟雾标记 / next slice
seed run-check <task> --slice S-NNN -- <命令>     # [assert] 真实执行声明命令，落盘 exit_code + 输出
seed run-check <task> --slice S-NNN \
  --judge "<slice 声明的 judge 项>" --verdict pass|fail \
  --trace "<裁决依据>" [--grade "..." --by "..."]   # [judge] 独立 agent 裁决后落盘
seed run-check <task> --slice S-NNN \
  --human "<slice 声明的 human 项>" \
  --note "<结论>" [--by "<签收人>" --evidence "<证据指针>"]  # [human] 真人签收记录
seed done <task> --slice S-NNN                   # 证据齐备后勾选 checkbox（唯一合法入口）
seed wiki index|search|collect|lint              # .wiki/ 索引 / 搜索 / 摘要 / 体检
```

## 三类验证 + 硬 gate（防 AI 偷懒）

验证项按"谁判定它对"分三类（封闭词汇，详见 `skills/references/conventions.md`）：

- **assert** — 会失败的断言命令（测试套件 / 契约回放 / Playwright spec）。gate = exit 0。
- **judge** — 独立 agent（fresh session，生成者≠验证者）按 AC rubric 裁决。gate = verdict=pass。
- **human** — 真人 stakeholder 签收。gate = 签收记录。

机械层：

- `run-check --` 的命令必须与 `slices/S-NNN.md` 声明完全一致——不接受替代或弱化；**烟雾命令**（裸 `curl`/`echo` 这类"跑过就算过"）可执行但会被警告，因为它们只证可达不证语义。
- `seed done` 只认落盘证据：assert 需 exit 0、judge 需 verdict=pass、human 需签收记录；缺口按 `[kind]` 逐条列出。
- gate 只保证"声明命令被执行并落盘"，**不保证语义正确**——语义可信度靠三类词汇 + 烟雾嗅探 + 独立 judge + review 共同把住。
- hook（`hooks/seed_guard.py`）拦截：手工勾选 checkbox、手写 `evidence/`、破坏性命令（`rm -rf`、`git reset --hard` 等）。

其余质量层（可证伪 AC、testability gate、review 对账、偷懒签名清单）是流程约定，写在对应 SKILL.md 里。

## 测试

```bash
cd plugins/seed-kit && python3 -m pytest tests/ -q
```
