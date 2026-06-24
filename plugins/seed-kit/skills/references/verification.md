# seed-kit 验证约定

brainstorm / impl / review 共读（research / wiki 不需要）。PRD 的交付面与覆盖、三类验证 kind、judge loop、rubric/score-file 格式、helper 硬规则都在这。

## 原则

- gate 管**声明义务**：assert 管可机械断言的正确性，judge 可用项目 rubric + score-file 管声明过的体验质量；未声明维度仍靠 review / 人判断，质量没有上限。

## 交付面 / 验证面

每个 `slices/S-NNN.md` 必须先声明 `## 交付面`——本 slice 实际交付的面。下面是常见 Web 产品的**参考词汇表（非封闭）**，项目可用任意面名（游戏 `gameplay`、CLI `cli-dx`、数据管道 `data-quality` 等）：

- `backend-domain` — 后端领域逻辑、模型、服务、聚合规则。
- `api` — API 合同、认证/权限、请求响应与失败路径。
- `web-ui` — 前端组件、表单、页面状态、浏览器可观察行为。
- `e2e` — 跨前后端主旅程。
- `compliance` — 合规、文案签收、备案/发布门槛。
- `infra` — 部署、配置、脚手架、CI/环境检查。

`## 验证面` 里的每条验证项写成**验收义务（obligation）**：`[kind][surface] <obligation-id>: <可观测行为>`。kind 表示“谁判定它对”，surface 表示“覆盖哪个交付面”（可多个：`[assert][backend-domain,api]`）。obligation-id 是这条义务的 slug（可带 `AC-N` 标签作 review 对账线索，helper 不解析 AC 全集）；冒号后是**可观测行为**——能观察、能判定对错。命令**不**写在这里，由 impl 用 `seed run-check --obligation <id> -- <会失败的断言>` 执行并绑定到义务。一条义务对应一个可证伪维度，不要用一条套件命令覆盖多个 AC 维度。

覆盖规则：helper **只校验“每个声明的交付面被至少一条验证项覆盖”**（集合关系，面名字无关——防漏覆盖/冒充，如声明 web-ui 却只标 backend-domain 的后端测试）。**helper 不按面名规定 kind**——“该面该用 assert 还是 judge/human“是项目标准（写 `.claude/rules`），交 review 查“验证降级”。烟雾命令仍由 helper 拦截（见下）。

覆盖要求：每个声明的交付面必须被至少一条验证项覆盖（helper 强制，面名字无关）；且验证要真的触及 AC 声称的每个维度——不要让一条线的通过冒充另一条线的覆盖（例：AC 含“正确路径 + 失败路径 + 边界”，只测正确路径不算整体已验证）。某维度不确定怎么验证时补 judge/human，不要默默漏掉。**helper 查不了“该声明却漏声明”**（如 AC 含 web-ui 但 slice 没声明它）——那是声明驱动的固有边界，靠 review 的产品级对账。

## 三类验证（封闭词汇）

每条验证项按“谁判定它对”归入一类，写在 `slices/S-NNN.md` 的 `## 验证面`：

- `[assert][surface] <id>: <行为>` — 命令本身是**会失败的断言**（测试套件、契约回放、Playwright spec）。impl 用 `--obligation <id> -- <命令>` 执行，exit 0 才 passed。**写法要求**：有状态 API 流写成一个自包含集成测试（内部 setup → act → assert），不要拆成多个靠 shell 变量传递状态的 curl 命令。第三方或不可达边界用录制好的 fixture / 契约断言，不静默跳过。
- `[judge][surface] <id>: <行为>` — 由**独立上下文的裁判**裁决（生成者≠验证者），看**真实产物**（截图/实时页面/实际输出）、不看代码。两种落盘：legacy 二值 `--verdict pass|fail`；推荐的 scoring gate 用项目 `--rubric` + 裁判 `--score-file`，helper 只校验 JSON 形状、artifact 存在并计算 verdict。rubric 的维度、门槛、参考来自项目；插件不解释这些维度。
- `[human][compliance] <id>: <行为>` — **真人 stakeholder** 签收，用于合规/备案等本质不可自动化交付面；human 覆盖可断言交付面是设计气味，由项目规则与 review 查验证降级。

原则：**assert 优先**——能用断言就不要用 judge，能 judge 就不要叠加 human。一个 slice 若所有验证都只是 `[human][compliance]`，是设计气味，brainstorm 要显式标记并说明理由。

`assert` 的命令必须真正断言：裸 `curl`（无 `--fail`/管道）、`echo`、`true` 这类“跑过就算过”的烟雾命令——run-check 时对**非 compliance 交付面**直接硬阻断（拒绝落盘），对 compliance 面允许但警告。它们只证可达/可执行，不证语义正确，不构成有效验证，也不能覆盖交付面。

旧式兼容：裸 `` `命令` `` 视为 `[assert]`，`[manual]` 视为 `[human]`，仍可解析；但没有 surface 标签时不覆盖任何交付面。

## 体验质量：judge 走 review loop（不做 gate 分）+ 项目标准

正确性靠 assert/human 等确定性证据（gate 守对错）；用户可感质量是"好坏"问题，用 `[judge]` 进 **review loop** 迭代收敛（loop 守好坏）——**不做 scoring gate 卡 done**。独立 judge 看真实产物、按项目 rubric 提体验 finding，迭代到找不到新问题；收敛靠"无新体验 finding"，不靠"达到 min 分"。详见 `CLAUDE.md`「验证哲学：gate 守对错，loop 守好坏」。

- **标准从项目**：打哪些维度、门槛、参考什么产品——读项目 `DESIGN.md`、`.claude/rules/`、PRD 质量基线或项目提供的 rubric JSON。
- **机制在插件**：helper 校验 rubric/score-file JSON、artifact 存在（供 judge 在 loop 里产出结构化评分）；不解释维度含义，也不内置审美。
- **rubric/score-file 的定位**：是 judge 在 loop 里评体验的结构化输入/产出，**不是卡 done 的 gate 门槛**。`seed done` = assert 全绿 + review loop 收敛（无 survived blocking），不是 judge verdict=pass。
- **多裁判 fan-out**：helper 已实装（`seed score aggregate`），作为 review loop 的多角度编排（review SKILL 三档强度之一），不是独立 gate 模式。

一句话：体验质量走 review loop（judge 迭代到无新 finding），不走 scoring gate；rubric/score-file 是 loop 里的结构化评分工具。

### Rubric 与 Score-file 格式

**Rubric**（项目定义，插件不内置）：

```json
{
  "id": "web-ui-quality-v1",
  "scale": {"min": 0, "max": 5},
  "aggregate": {"min_average": 3.5},
  "dimensions": {
    "visual_language": {
      "min": 3,
      "weight": 1.0
    },
    "information_hierarchy": {
      "min": 3,
      "weight": 1.5
    }
  }
}
```

- `dimensions.<name>.min`：该维度的地板门槛（必须）
- `dimensions.<name>.weight`：加权平均的权重（可选，默认 1.0）
- `aggregate.min_average`：整体平均线门槛（可选）

**Score-file**（独立 judge 生成）：

```json
{
  "rubric_id": "web-ui-quality-v1",
  "scores": {
    "visual_language": {
      "score": 4,
      "rationale": "视觉语言统一，符合 DESIGN.md 的家庭数据台基线"
    },
    "information_hierarchy": 3
  }
}
```

- 兼容两种格式：`{score, rationale}`（推荐）或纯数值（legacy）
- **rationale 必填**（新格式）：评分依据，进 evidence 供 review 追溯
- **weight 由 rubric 定义**：score-file 只记录分数，不记录权重

## 硬规则（helper / hook 保证，不需要靠记忆）

- `run-check` 按 `--obligation <id>` 把证据绑到 slice 声明的义务（三 kind 共用）；obligation 格式下命令不写在 slice，由 impl 绑定。烟雾命令（裸 `curl`/`echo`）对**非 compliance 交付面**硬阻断（拒绝落盘），compliance 面允许但警告。
- `done` 只认落盘证据：assert 项需 passed（exit 0），judge 项需 verdict=pass（legacy 手写或 scoring gate 计算），human 项需 note + 签收记录；缺口按 `[kind]` 逐条列出。
- judge 必须由独立上下文裁决后记录——helper 只落盘/校验 verdict 或 scoring evidence，不调用 LLM。
- `done` 勾选 = **声明义务已过 gate**：包含已声明的 scoring judge 达到项目 rubric；不代表未声明维度达标，也不代表质量没有上限。
- 不要手工编辑 checkbox 或 `evidence/`（会被 hook 拦截）。
