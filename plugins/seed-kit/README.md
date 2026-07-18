# seed-kit

轻量 PRD-first 工作流。五个 skill 全部由用户主动触发、互不自动耦合；进度状态以 `prd.md` 的 slice checkbox 为准，没有 task.json 或阶段状态机。

设计动机与取舍见 [`DESIGN.md`](DESIGN.md)。

## 评估（seed-kit-evals）

本插件的行为回归与自进化实验室在独立仓库 **seed-kit-evals**（不是本目录内的 pytest）。

- **现行操作手册（给 AI / 人类）** → [`EVALS.md`](EVALS.md)
- 旧 harness 历史快照（勿当操作手册）→ [`EVAL_HANDOFF.md`](EVAL_HANDOFF.md)
- 默认路径：`/Users/camellia/Personal/Code/claude/seed-kit-evals`
- 跑评测时通过 `--plugin-dir` 加载本目录；语义场景另需 `GAUNTLET_ROOT`

```bash
export PATH="$HOME/.bun/bin:$PATH"
cd /Users/camellia/Personal/Code/claude/seed-kit-evals
bun run src/cli/index.ts run-all --tier sentinel --agents claude --providers ali-qwen \
  --plugin-dir /Users/camellia/Personal/Code/claude/claude-plugins/plugins/seed-kit
```

## 五个 skill

| skill | 职责 | 产出 |
|---|---|---|
| research | 给需求收集外部资料（竞品、API、数据源） | `.arbor/research/<topic>/`（index.md / raw/ / notes/） |
| brainstorm | 访谈式收敛需求：一次一问 + 推荐答案 | `.arbor/tasks/<task>/prd.md`（可证伪 AC + 品质意图 + 有序 Slices） |
| impl | 逐 slice 执行 PRD，硬事实通过才勾选完成 | 代码 |
| review | 干净视角逐验收条目对账 diff，专查偷懒签名 | 追加 `review.md` |
| wiki | 项目知识层：长期资料 + 多文件链路知识 | `.arbor/.wiki/` 页面 |

skill 之间没有自动流转：brainstorm 不主动搜索 research，impl 不主动查 wiki，review 由用户主动触发。

## 状态模型

```
.arbor/tasks/<task>/
├── prd.md           # 进度 source of truth：slice 内联（### [ ] S-NNN heading + prose）
├── review.md        # review 追加记录
├── done-logs/       # seed done 机械验证记录
├── review-loop.json # 显式 task 级 review-loop 终态（可选）
└── notes/           # impl 过程备注（可选）
```

单一进度归属：PRD checkbox 表示 slice 进度；`done-logs/` 与 `review-loop.json` 分别记录机械验证和显式循环终态，不构成第二套阶段状态。断点续作 = `seed status <task>` + git log。

## seed CLI（核心 3 个命令 + wiki 家族）

```bash
seed new <task>                                       # 脚手架任务目录 + prd.md 模板
seed status [<task>] [--json]                         # 进度 / 结构校验 / next slice
seed done <task> --slice S-NNN --test "<cmd>" \
  [--quality "<cmd>"]...                              # 跑 agent 传入的测试+质量命令，全过则翻 checkbox
seed review-mark <task> --verdict <reason> [--round N] # 落 review-loop 终态 marker
seed score aggregate --rubric <rubric.json> \
  --score-files <file1.json> <file2.json> ... \
  --out <aggregate.json>                              # 聚合多个 score-file（多裁判模式）
seed wiki index|search|collect|lint                   # .arbor/.wiki/ 工具
```

## 验证设计

Slice 内联在 PRD 的 `### [ ] S-NNN` heading 下，验收用 `* [ ]` 条目写——每条一个可测试的行为路径。形式自由，每条能独立对应一个测试用例。

### Gate 只卡硬事实

`seed done` 执行 agent 显式传入的 `--test` 与可重复 `--quality` 命令；测试命令若是 `true`/`echo` 等显而易见的空操作会被拒绝。全过 → 翻 checkbox。

### Loop 守好坏

review-loop 做整体判断——对着 PRD 全文判断交付是否兑现了意图，迭代到收敛。

三类验证手段（概念分类）：
- **assert** — 机械断言。项目测试框架，exit 非零即失败。`seed done` 执行。
- **judge** — 独立裁判。看真实产物，按 PRD 中描述的方向 + DESIGN.md + rubric 评。走 review-loop，不进 gate。
- **human** — 真人签收。用于本质不可自动化事项。

hook（`hooks/seed_guard.py`）拦截：手工勾选 checkbox、破坏性命令。

## 测试

```bash
cd plugins/seed-kit && python3 -m pytest tests/ -q
```
