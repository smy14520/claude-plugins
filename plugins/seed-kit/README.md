# seed-kit

轻量 PRD-first 工作流。五个 skill 全部由用户主动触发、互不自动耦合；状态就是 `prd.md` 的 slice checkbox + `evidence/` 证据文件，没有状态机、没有 task.json。

设计动机与取舍见 [`DESIGN.md`](DESIGN.md)。

## 五个 skill

| skill | 职责 | 产出 |
|---|---|---|
| research | 给需求收集外部资料（竞品、API、数据源） | `.arbor/research/<topic>/`（index.md / raw/ / notes/） |
| brainstorm | 访谈式收敛需求：一次一问 + 推荐答案 | `.arbor/tasks/<task>/prd.md`（可证伪 AC + 有序 Slices） |
| impl | 逐 slice 执行 PRD，证据齐备才能勾选完成 | 代码 + `evidence/` |
| review | 干净视角逐 AC 对账 diff，专查偷懒签名 | 追加 `review.md` |
| wiki | 项目知识层：长期资料 + 多文件链路知识 | `.wiki/` 页面 |

skill 之间没有自动流转：brainstorm 不主动搜索 research，impl 不主动查 wiki，review 由用户主动触发。

## 状态模型

```
.arbor/tasks/<task>/
├── prd.md        # 需求 source of truth；## Slices = 有序 checkbox 索引（唯一进度状态）
├── slices/       # S-NNN.md：每个 slice 的验收与验证项（内容唯一的家）
├── review.md     # review 追加记录
├── evidence/     # seed run-check 落盘：S-NNN/<seq>-<kind>.json + .log
└── notes/        # impl 过程备注（可选）
```

单一归属：顺序与状态记录在 prd.md 索引，slice 内容记录在 `slices/S-NNN.md`，没有任何事实写两遍；`seed status` 机械校验索引行 ↔ slice 文件一致。断点续作 = `seed status <task>` + git log。代码就是进度。

## seed CLI（核心 4 个命令 + wiki 家族）

```bash
seed new <task>                                  # 脚手架任务目录 + prd.md / slices/S-001.md 模板
seed status [<task>] [--json]                    # 进度 / 证据状态 / 结构校验 / 烟雾标记 / next slice
seed run-check <task> --slice S-NNN --obligation <id> -- <命令>   # [assert] 真实执行，落盘 exit_code + 输出
seed run-check <task> --slice S-NNN \
  --obligation <id> --verdict pass|fail --trace "<裁决依据>" \
  --artifact "<看过的截图>" [--grade "..." --by "..."]   # [judge] legacy 二值裁决
seed run-check <task> --slice S-NNN \
  --obligation <id> --rubric <rubric.json> --score-file <score.json> \
  --trace "<评分依据>" --artifact "<看过的截图>" [--by "..."]   # [judge] scoring gate，helper 计算 verdict
seed run-check <task> --slice S-NNN \
  --obligation <id> --note "<结论>" [--by "<签收人>" --evidence "<证据指针>"]  # [human] 真人签收记录
seed done <task> --slice S-NNN                   # 证据齐备后勾选 checkbox（唯一合法入口）
seed wiki index|search|collect|lint              # .wiki/ 索引 / 搜索 / 摘要 / 体检
```

## 交付面 + 三类验证 + 硬 gate（防 AI 偷懒）

每个 slice 显式声明 `## 交付面`（参考词汇表 backend-domain / api / web-ui / e2e / compliance / infra，项目可扩展），验证项写成验收义务 `[kind][surface] <obligation-id>: <可观测行为>`：

- **surface** — 覆盖哪个交付面；helper 做确定性结构约束，防止后端测试冒充 Web / UI / E2E 覆盖。
- **assert** — 会失败的断言命令（测试套件 / 契约回放 / Playwright spec）。gate = exit 0。
- **judge** — 由独立 agent 裁决（生成者≠验证者，详见 verification），看真实产物按项目 rubric 裁决。legacy gate = `verdict=pass`；scoring gate = helper 读取 `--rubric` + `--score-file` 并计算 verdict。`--artifact` 指向看过的产物，helper 校验存在。
- **human** — 真人 stakeholder 签收，仅用于 compliance 等不可自动化交付面。gate = 签收记录。

机械层：

- `seed status` 检查每个交付面是否有有效验证覆盖；human 覆盖可断言交付面是设计气味，但 helper 不机械禁止，由项目规则与 review 查验证降级。
- `run-check --obligation <id>` 把证据绑到 slice 声明的义务（命令不写在 slice，由 impl 绑定）；**烟雾命令**（裸 `curl` / `echo` 这类“跑过就算过”）对非 compliance 交付面硬阻断，对 compliance 面警告——它们只证可达不证语义，不能算作有效覆盖。
- `seed done` 只认落盘证据：assert 需 exit 0、judge 需 verdict=pass（legacy 手写或 scoring gate 计算）、human 需签收记录；缺口按 `[kind]` 逐条列出。
- gate 只保证“声明的 evidence 形状与结果达标”，**不保证语义正确**——语义可信度由交付面结构约束、三类词汇、烟雾嗅探、独立 judge、artifact、review 共同保证。
- `seed done` / 绿看板 = **声明义务已过 gate**：包含声明过的 scoring judge 达到项目 rubric；但不代表未声明的体验维度达标，也不代表质量没有上限。
- hook（`hooks/seed_guard.py`）拦截：手工勾选 checkbox、手写 `evidence/`、破坏性命令（`rm -rf`、`git reset --hard` 等）。

其余质量层（可证伪 AC、testability gate、review 对账、偷懒签名清单）是流程约定，写在对应 SKILL.md 里。

## 测试

```bash
cd plugins/seed-kit && python3 -m pytest tests/ -q
```
