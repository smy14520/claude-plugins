# seed-kit

轻量 PRD-first 工作流。五个 skill 全部由用户主动触发、互不自动耦合；状态就是 `prd.md` 的 slice checkbox，没有状态机、没有 task.json。

设计动机与取舍见 [`DESIGN.md`](DESIGN.md)。

## 五个 skill

| skill | 职责 | 产出 |
|---|---|---|
| research | 给需求收集外部资料（竞品、API、数据源） | `.arbor/research/<topic>/`（index.md / raw/ / notes/） |
| brainstorm | 访谈式收敛需求：一次一问 + 推荐答案 | `.arbor/tasks/<task>/prd.md`（可证伪 AC + 品质意图 + 有序 Slices） |
| impl | 逐 slice 执行 PRD，硬事实通过才勾选完成 | 代码 |
| review | 干净视角逐验收条目对账 diff，专查偷懒签名 | 追加 `review.md` |
| wiki | 项目知识层：长期资料 + 多文件链路知识 | `.wiki/` 页面 |

skill 之间没有自动流转：brainstorm 不主动搜索 research，impl 不主动查 wiki，review 由用户主动触发。

## 状态模型

```
.arbor/tasks/<task>/
├── prd.md        # 唯一状态：slice 内联（### [ ] S-NNN heading + prose）
├── review.md     # review 追加记录
├── done-logs/    # seed done 日志
└── notes/        # impl 过程备注（可选）
```

单一归属：PRD 是唯一文件，slice 内联在 `### [ ] S-NNN` heading 下。断点续作 = `seed status <task>` + git log。代码就是进度。

## seed CLI（核心 3 个命令 + wiki 家族）

```bash
seed new <task>                                       # 脚手架任务目录 + prd.md 模板
seed status [<task>] [--json]                         # 进度 / 质量命令 / 结构校验 / next slice
seed done <task> --slice S-NNN                        # 跑项目测试+质量命令+验产物，全过则翻 checkbox
seed review-mark <task> --verdict <reason> [--round N] # 落 review-loop 终态 marker
seed score aggregate --rubric <rubric.json> \
  --score-files <file1.json> <file2.json> ... \
  --out <aggregate.json>                              # 聚合多个 score-file（多裁判模式）
seed wiki index|search|collect|lint                   # .wiki/ 工具
```

## 验证设计

Slice 内联在 PRD 的 `### [ ] S-NNN` heading 下，验收用 `* [ ]` 条目写——每条一个可测试的行为路径。形式自由，每条能独立对应一个测试用例。

### Gate 只卡硬事实

`seed done` 从项目配置文件自动检测测试+质量命令，逐条执行。全过 → 翻 checkbox。

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
