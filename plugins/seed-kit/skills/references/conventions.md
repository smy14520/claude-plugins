# seed-kit 通用约定

使用语言：中文。

## 原则

- 五个 skill（research / brainstorm / impl / review / wiki）全部由用户主动触发，互不自动联动：不要主动去搜 research、查 wiki、推进下一阶段，除非用户明确指定。
- `prd.md` 是需求 source of truth：`## Slices` 是有序 checkbox 索引（顺序与状态唯一的家）；每个 slice 的验收与验证项住在 `slices/S-NNN.md`（内容唯一的家）。进度状态 = 索引 checkbox + `evidence/`；git log 是代码进度。没有其他状态文件。
- agent 不自动 commit；在合适的节点提示用户 commit。

## 目录

```
.arbor/tasks/<task>/      # prd.md / slices/ / review.md / evidence/ / notes/
.arbor/research/<topic>/  # index.md / raw/ / notes/
.wiki/                   # 项目知识层（导航层，非 source of truth）
```

## 交付面 / 验证面

每个 `slices/S-NNN.md` 必须先声明 `## 交付面`，闭集如下：

- `backend-domain` — 后端领域逻辑、模型、服务、聚合规则。
- `api` — API 合同、认证/权限、请求响应与失败路径。
- `web-ui` — 前端组件、表单、页面状态、浏览器可观察行为。
- `e2e` — 跨前后端主旅程。
- `compliance` — 合规、文案签收、备案/发布门槛。
- `infra` — 部署、配置、脚手架、CI/环境检查。

`## 验证面` 里的每条验证项写成 `[kind][surface] target`。kind 表示“谁判定它对”，surface 表示“覆盖哪个交付面”。一个验证项可覆盖多个面：`[assert][backend-domain,api]`。

覆盖规则：backend-domain / api / infra 需要非烟雾 `[assert]`；web-ui 可用 UI 测试形状的 `[assert]` 或 `[judge]`；e2e 需要 Playwright/Cypress/Dusk/e2e 形状的 `[assert]`；compliance 可用 `[assert]` / `[judge]` / `[human]`。human 不能替代 backend-domain / api / web-ui / e2e / infra。

## 三类验证（封闭词汇）

每条验证项按“谁判定它对”归入一类，写在 `slices/S-NNN.md` 的 `## 验证面`：

- `[assert][surface] \`命令\`` — 命令本身是**会失败的断言**（测试套件 / 契约回放 / Playwright spec）。seed 真实执行，exit 0 才 passed。
- `[judge][surface] 描述` — 由**独立 agent**（fresh session，生成者≠验证者）按 AC rubric 裁决，落盘 verdict。
- `[human][compliance] 描述` — **真人 stakeholder** 签收，仅用于合规/备案等不可自动化交付面。

原则：**assert 优先**——能用断言就别用 judge，能 judge 就别堆 human。一个 slice 只能 `[human][compliance]` 验证是设计气味，brainstorm 要显式标记并说明理由。

`assert` 的命令必须真正断言：裸 `curl`（无 `--fail`/管道）、`echo`、`true` 这类“跑过就算过”的烟雾命令会被 seed 标记警告——它们只证可达/可执行，不证语义正确，不构成有效验证，也不能覆盖交付面。

旧式兼容：裸 `` `命令` `` 视为 `[assert]`，`[manual]` 视为 `[human]`，仍可解析；但没有 surface 标签时不覆盖任何交付面。

## seed CLI

`seed` 入口：`${CLAUDE_PLUGIN_ROOT}/bin/seed`（也可 `python3 ${CLAUDE_PLUGIN_ROOT}/tools/seed.py`），在项目根目录运行。

```bash
seed new <task>                                  # 脚手架任务目录 + prd.md / slices/S-001.md 模板
seed status [<task>] [--json]                    # 进度 / 证据状态 / 结构校验 / 烟雾标记 / next slice
seed run-check <task> --slice S-NNN -- <命令>     # [assert] 真实执行声明命令，落盘 exit_code + 输出
seed run-check <task> --slice S-NNN \
  --judge "<slice 声明的 judge 项原文>" \
  --verdict pass|fail --trace "<裁决依据/证据指针>" [--grade "..." --by "<裁决者>"]
seed run-check <task> --slice S-NNN \
  --human "<slice 声明的 human 项原文>" \
  --note "<验证了什么、结论>" [--by "<签收人>" --evidence "<证据指针>"]
seed done <task> --slice S-NNN                   # 证据齐备后勾选 checkbox（唯一合法入口）
seed wiki index|search|collect|lint              # .wiki/ 工具
```

硬规则（由 helper 与 hook 保证，不需要靠记忆）：

- `run-check --` 的命令必须与 `slices/S-NNN.md` 声明完全一致，不接受替代/弱化命令；烟雾命令可执行但会被警告。
- `done` 只认落盘证据：assert 项需 passed（exit 0），judge 项需 verdict=pass，human 项需 note + 签收记录；缺口按 `[kind]` 逐条列出。
- judge 必须由独立 session 的 agent 裁决后记录——helper 只落盘/校验 verdict，不调用 LLM。
- 不要手工编辑 checkbox 或 `evidence/`（会被 hook 拦截）。
