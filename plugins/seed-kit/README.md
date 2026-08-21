# seed-kit

轻量 PRD-first 工作流。十个 skill 之间：进入要么用户发起，要么 agent 提议后用户同意，绝不单方进入（例外：PRD 定稿后 brainstorm 自动派 seed-prd-review 独立审查）；进度状态以 `prd.md` 的 slice checkbox 为准，没有 task.json，也没有阶段状态机（`impl-state.json` 是任务档案：锚点 + handoff + 证据指针；`gate-attempts/` 是失败留痕——都不构成第二套进度）。

设计动机与取舍见 [`DESIGN.md`](DESIGN.md)。

## 评估（seed-kit-evals-v2）

本插件的行为回归与效果对比实验室在独立仓库 **seed-kit-evals-v2**（不是本目录内的 pytest）。

- **本目录使用说明(快速上手)** → [`EVALS.md`](EVALS.md)
- **完整手册** → `/Users/camellia/Personal/Code/claude/seed-kit-evals-v2/EVALS.md`;活跃套件与理由 → 同仓库 `scenarios/MANIFEST.md`
- 旧版实验室 `seed-kit-evals`（v1）与 [`EVALS_V1.md`](EVALS_V1.md) 为历史资料；新工作一律走 v2

```bash
# 一次配置 config/local.json 后，日常只需：
/Users/camellia/Personal/Code/claude/seed-kit-evals-v2/bin/seed-evals doctor       # 环境自检
/Users/camellia/Personal/Code/claude/seed-kit-evals-v2/bin/seed-evals sentinel     # 分钟级冒烟回归
/Users/camellia/Personal/Code/claude/seed-kit-evals-v2/bin/seed-evals value <exp>  # 效果对比实验
```


## 十个 skill

| skill | 职责 | 产出 |
|---|---|---|
| research | 给需求收集外部资料（竞品、API、数据源） | `.arbor/research/<topic>/`（index.md / raw/ / notes/） |
| brainstorm | 访谈式收敛需求：一次一问 + 推荐答案；入场先判断开图还是直接访谈 | `.arbor/tasks/<task>/prd.md`（可证伪 AC + 品质意图 + 有序 Slices） |
| wayfinder | 大且雾任务开决策图：决策链拆成票跨会话一张张拍，frontier 由 `seed map status` 从盘上推导，图清交棒 brainstorm 收敛 | `.arbor/maps/<slug>/`（map.md 索引 + tickets/ 决策票） |
| impl | 逐 slice 执行 PRD，硬事实通过才勾选完成；handoff/证据落任务档案供续接 | 代码 + 任务档案 |
| check | 收尾自查：对照原始需求逐条声称问归属（AC / 用户确认的 OoS / 缺口）+ 轻量快扫 | 归属表 + 缺口拍板记录 |
| review | 干净视角逐验收条目对账 diff，专查偷懒签名 | 追加 `review.md` |
| wiki | 项目知识层：长期资料 + 多文件链路知识 | `.arbor/.wiki/` 页面 |
| init | 新项目初始化时推荐默认基准（Fowler 12 味代码审查基准） | 项目标准文件（CLAUDE.md / .claude/rules/） |
| handoff | 把当前会话压缩成交接文档，供另一个 AI / 新会话续接 | OS 临时目录的 handoff 文档 |
| architect | 以架构师立场审 PRD 或代码：放置裁决 / 不可逆预警 / 形态退化，只建议不改码，结论交用户拍板 | 审计报告（对话交付；留痕可选：architect.md / wiki） |

skill 间流转经用户确认后当场进入（agent 建议 → 用户点头，不要求重新点名）；brainstorm 收尾自动派 seed-prd-review 做 PRD 独立审查（对账 Design 承诺的落地点），有 serious gap 修完再停；impl 开工、review-loop 深审与 architect 架构审计是重入口，仍由用户显式点名。impl 会读取 wiki 索引，并在全量模式全部 slice done 后由编排者内联收尾自查（按 check 清单做题面对照 + 兑现对账），落 `review-mark --depth inline`；触及高风险面或拿不准时升级派 seed-review（`--depth single`）；review-loop（5 agent 对抗深审）与 judge（产物评审）是**增强项，默认不跑**，用户显式点名才跑；review skill 本身仍由用户主动触发。`.arbor/maps/` 是决策账本：票不进 `seed done`、不翻 checkbox、不是 slice，不构成第二套进度，图清即冻结。

## 状态模型

目录结构与各文件职责的唯一权威在 [`skills/references/conventions.md`](skills/references/conventions.md)「目录」。

单一进度归属：PRD checkbox 表示 slice 进度；`done-logs/`（只有成功）、`gate-attempts/`（失败留痕）与 `review-loop.json` 分别记录机械验证、失败尝试和显式循环终态，不构成第二套阶段状态。断点续作 = `seed status <task>` + git log。

## seed CLI

命令面以 `seed --help` 为准（活文档，代码保证不漂移）；速查表见 [`skills/references/conventions.md`](skills/references/conventions.md)。

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
