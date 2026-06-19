# seed-kit 通用约定

使用语言：中文。

## 原则

- 五个 skill（research / brainstorm / impl / review / wiki）全部由用户主动触发，互不自动联动：不要主动去搜 research、查 wiki、推进下一阶段，除非用户明确指定。
- `prd.md` 是需求 source of truth：`## Slices` 是有序 checkbox 索引（顺序与状态唯一的家）；每个 slice 的验收与验证项住在 `slices/S-NNN.md`（内容唯一的家）。进度状态 = 索引 checkbox + `evidence/`；git log 是代码进度。没有其他状态文件。
- agent 不自动 commit；在合适的节点提示用户 commit。
- gate 管**正确性**，不管**体验质量**：`seed done` 只保证正确且不回归；好不好用/好不好看这类不可验证质量靠独立高标 judge 在环 + 生成自由把关，不压在 gate 上。
- **标准分层（机制在插件，标准在项目）**：插件只给栈无关机制（三类验证 / 交付面封闭集 / 覆盖规则 / 烟雾嗅探 / `seed` CLI）。项目标准自管，分三处：**测试纪律**（测试工具、UI 是否要求交互断言、覆盖门槛、DoD）放 `.claude/rules/`（如 `testing.md`，可用 `paths:` frontmatter 只在相关文件加载）；**品味/设计语言**（参考产品、配色字体、质量门槛）放 `DESIGN.md`；`CLAUDE.md` 做入口与 `@import` 引用。skill 设验证面 / 写测试 / 对账时读它们；项目没给标准时插件只兜通用地板（反毛坯房）。

## 目录

```
.arbor/tasks/<task>/      # prd.md / slices/ / review.md / evidence/ / notes/
.arbor/research/<topic>/  # index.md / raw/ / notes/
.wiki/                   # 项目知识层（导航层，非 source of truth）
```

## 交付面 / 验证面

每个 `slices/S-NNN.md` 必须先声明 `## 交付面`——本 slice 实际交付的面。下面是常见 Web 产品的**参考词汇表（非封闭）**，项目可用任意面名（游戏 `gameplay`、CLI `cli-dx`、数据管道 `data-quality` 等）：

- `backend-domain` — 后端领域逻辑、模型、服务、聚合规则。
- `api` — API 合同、认证/权限、请求响应与失败路径。
- `web-ui` — 前端组件、表单、页面状态、浏览器可观察行为。
- `e2e` — 跨前后端主旅程。
- `compliance` — 合规、文案签收、备案/发布门槛。
- `infra` — 部署、配置、脚手架、CI/环境检查。

`## 验证面` 里的每条验证项写成**验收义务（obligation）**：`[kind][surface] <obligation-id>: <可观测行为>`。kind 表示“谁判定它对”，surface 表示“覆盖哪个交付面”（可多个：`[assert][backend-domain,api]`）。obligation-id 是这条义务的 slug（可带 `AC-N` 标签作 review 对账线索，helper 不解析 AC 全集）；冒号后是**可观测行为**——能观察、能判定对错。命令**不**写在这里，由 impl 用 `seed run-check --obligation <id> -- <会失败的断言>` 执行并绑定到义务。一条义务对应一个可证伪维度，别用一条套件命令糊弄多个 AC 维度。

覆盖规则：helper **只校验"每个声明的交付面被至少一条验证项覆盖"**（集合关系，面名字无关——防漏覆盖/冒充，如声明 web-ui 却只标 backend-domain 的后端测试）。**helper 不按面名规定 kind**——"该面该用 assert 还是 judge/human"是项目标准（写 `.claude/rules`），交 review 查"验证降级"。烟雾命令仍由 helper 挡（见下）。

覆盖要求：每个声明的交付面必须被至少一条验证项覆盖（helper 强制，面名字无关）；且验证要真的触及 AC 声称的每个维度——别让一条线的通过冒充另一条线的覆盖（例：AC 含"正确路径 + 失败路径 + 边界"，只测正确路径不算整体已验证）。某维度不确定怎么验证时补 judge/human，不要默默漏掉。**helper 查不了"该声明却漏声明"**（如 AC 含 web-ui 但 slice 没声明它）——那是声明驱动的固有边界，靠 review 的产品级对账。

## 三类验证（封闭词汇）

每条验证项按“谁判定它对”归入一类，写在 `slices/S-NNN.md` 的 `## 验证面`：

- `[assert][surface] <id>: <行为>` — 命令本身是**会失败的断言**（测试套件 / 契约回放 / Playwright spec）。impl 用 `--obligation <id> -- <命令>` 执行，exit 0 才 passed。**写法**：有状态 API 流写成一个自包含集成测试（内部 setup→act→assert），不要写一串跨命令、靠 shell 变量串状态的 curl；第三方/不可达边界用录制好的 fixture / 契约断言，不静默跳过。
- `[judge][surface] <id>: <行为>` — 由**独立 agent** 裁决（agent team 的 reviewer / subagent / workflow review agent——独立 context，未被 impl 推理污染，生成者≠验证者；选哪种见 review SKILL），落盘 verdict。judge 看**渲染后的真实产物**（截图/实时页面/实际输出）、不看代码；裁完用 `--obligation <id> --verdict pass|fail --artifact <文件>` 附上看过的截图/输出，helper 校验它真实存在。web-ui 整体体验用高标开放 rubric（设计质量+原创性，打低“通用 AI 味”），不是功能清单。其余文档/skill 提 judge 裁决者时引用此处，不重复执行细节。
- `[human][compliance] <id>: <行为>` — **真人 stakeholder** 签收，仅用于合规/备案等不可自动化交付面。

原则：**assert 优先**——能用断言就别用 judge，能 judge 就别堆 human。一个 slice 只能 `[human][compliance]` 验证是设计气味，brainstorm 要显式标记并说明理由。

`assert` 的命令必须真正断言：裸 `curl`（无 `--fail`/管道）、`echo`、`true` 这类“跑过就算过”的烟雾命令——run-check 时对**非 compliance 交付面**直接硬挡（拒绝落盘），对 compliance 面允许但警告。它们只证可达/可执行，不证语义正确，不构成有效验证，也不能覆盖交付面。

旧式兼容：裸 `` `命令` `` 视为 `[assert]`，`[manual]` 视为 `[human]`，仍可解析；但没有 surface 标签时不覆盖任何交付面。

## 体验质量：地板 + judge 在环（fan-out 评分是设计方向，未实装）

正确性靠 gate（assert/judge/human，见上）；**体验质量是另一条腿**，不进 gate。**当前实装**：`[judge]` 看真实产物、`--artifact` 附证据、二值 verdict（见上节 + review skill）。下面是**设计方向（未实装）**，待 review skill 的 fan-out 评分循环落地后再激活——现在不要照它执行：

- **触发（方向）**：impl 把一个 slice 的 assert 跑绿后，看它的 `## 交付面`——每个**可感面**跑一次质量评分。trigger 在 slice（`## 交付面`），不由 impl 自行决定做不做。
- **标准从项目**：打哪些维度、bar、参考什么产品——读项目 `DESIGN.md` / PRD 质量基线。**插件不硬编码任何栈的审美/质量标准。**
- **机制（方向，未实装）**：每个面派独立 scorer，感知真实产物 → 按项目标准打分 → 不到 bar 回灌 impl 改 → 重打（bounded）。落盘 artifact 待定（候选：复用 `review.md` 追加；新增 `quality.md` 目前无 producer/consumer，**未引入**）。
- **通用地板（已适用；是体验质量纪律，区别于 gate 管的正确性；不是品味）**：项目无 `DESIGN.md` 时的兜底——不交占位文案/Lorem/裸 HTML、空/加载/错误态齐全、不崩、没有明显"通用 AI 味"（如紫渐变白卡）。写成**方向 + 反例**，不是清单。品味（参考产品/设计语言）仍靠项目或 AI 在地板之上自由发挥。

一句话：当前 = gate（正确性）+ judge 在环 + 通用地板；fan-out 评分循环是计划中的演进，**未实装**。

## seed CLI

`seed` 入口：`${CLAUDE_PLUGIN_ROOT}/bin/seed`（也可 `python3 ${CLAUDE_PLUGIN_ROOT}/tools/seed.py`），在项目根目录运行。

```bash
seed new <task>                                  # 脚手架任务目录 + prd.md / slices/S-001.md 模板
seed status [<task>] [--json]                    # 进度 / 证据状态 / 结构校验 / 烟雾标记 / next slice
seed run-check <task> --slice S-NNN --obligation <id> -- <命令>   # [assert] 真实执行，绑定到 obligation，落盘 exit_code + 输出
seed run-check <task> --slice S-NNN \
  --obligation <id> --verdict pass|fail --trace "<裁决依据/证据指针>" [--artifact "<看过的截图/输出>" --grade "..." --by "<裁决者>"]   # [judge]
seed run-check <task> --slice S-NNN \
  --obligation <id> --note "<验证了什么、结论>" [--by "<签收人>" --evidence "<证据指针>"]   # [human]
seed done <task> --slice S-NNN                   # 证据齐备后勾选 checkbox（唯一合法入口）
seed wiki index|search|collect|lint              # .wiki/ 工具
```

硬规则（由 helper 与 hook 保证，不需要靠记忆）：

- `run-check` 按 `--obligation <id>` 把证据绑到 slice 声明的义务（三 kind 共用）；obligation 格式下命令不写在 slice，由 impl 绑定。烟雾命令（裸 `curl`/`echo`）对**非 compliance 交付面**硬挡（拒绝落盘），compliance 面允许但警告。
- `done` 只认落盘证据：assert 项需 passed（exit 0），judge 项需 verdict=pass，human 项需 note + 签收记录；缺口按 `[kind]` 逐条列出。
- judge 必须由独立 agent（agent team 的 reviewer 或 subagent）裁决后记录——helper 只落盘/校验 verdict，不调用 LLM。
- `done` 勾选 = **正确且不回归**，不代表体验质量达标。测试是地板不是天花板：可验证的正确性靠 gate，不可验证的体验质量靠“独立高标 judge 看真实产物在环 + 生成自由 + 参考注入品味”，gate 不保证后者。
- 不要手工编辑 checkbox 或 `evidence/`（会被 hook 拦截）。
