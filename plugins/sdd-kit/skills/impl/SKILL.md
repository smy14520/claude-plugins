---
name: impl
description: "Execute a task (or ad-hoc goal) as actual code changes. Picks a task from `.claude/tasks/<name>.tasks.md`, writes code to meet its acceptance, runs its own acceptance commands (self-check, not semantic review), reports with a strict 4-state machine (DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED). Never claims DONE without passing `acceptance:` commands. Never silently makes design decisions — ambiguity forces NEEDS_CONTEXT. Semantic audit against spec is the review skill's job, not impl's. Appends status line to the task file. Works without a task file too. Invoke only on explicit user request (e.g. '用 impl skill 执行 <task-id>')."
---

# Impl — 任务执行器（四状态报告）

将任务执行为代码。在声称 DONE 之前，必须运行任务自身的验收命令。绝不可以将 BLOCKED 悄悄降级为 DONE。

## 在五阶段工作流中的定位

```
research → spec → task → [impl] → review
                           ↓          ↑
                           └─ 仅自检（机械性）
                              语义审计属于 review skill
```

Impl 是**执行**阶段。它：

- 读取任务（从文件或会话中）
- 编写代码以满足验收标准
- 运行任务自身的验收命令（**自检**，机械性）
- 以四状态机报告状态
- **不**修改任务列表；**不**做设计决策
- **不**对 spec 进行语义审计——那是 `review` skill 的职责

## 四个原语

根据用户意图匹配对应原语；完整流程参见 [references/workflow.md](references/workflow.md)。

### 🎯 Pick — 选择任务

触发："实施 T-003"、"执行下一个 task"、"run next task"。

> **推理节奏**：🥐 **轻量**。选择 + 资格检查，属于机械性操作。

流程：

1. 定位 `.claude/tasks/<file>.tasks.md`（由用户指定，或扫描最近文件）
2. 读取任务列表 + 现有状态日志
3. 选择下一个可执行任务：`depends-on` 全部处于 `DONE` 状态，任务本身尚未完成或阻塞
4. 向用户确认："下一个: T-003 `<title>` — 预估 3h。开始？"

若无任务文件：退回临时模式（`references/workflow.md#ad-hoc`）。

### 🔨 Execute — 编写代码

触发：Pick 之后，或直接开始。

> **推理节奏**：🥐 **轻量**。你是翻译者，不是设计者——任务的 `deliverable` + `acceptance` 就是契约。如果翻译过程不是机械性的，那说明存在歧义，你应该发出 `NEEDS_CONTEXT`，而不是花更多力气思考。在这里节省 token；重度语义推理属于 `review` skill（单独调用，独立上下文）。

流程：

1. 读取任务的 `deliverable` + `acceptance` + `notes`
2. 按需读取 spec（仅获取上下文，不做二次决策）
3. 编写代码，目标是通过验收标准
4. 若出现歧义 → 立即停止并发出 NEEDS_CONTEXT（参见 state-machine.md）

### ✅ SelfCheck — 运行任务自身的验收命令

触发：Execute 之后，始终在报告 DONE 之前执行。

> **推理节奏**：🥐 **轻量、严格**。机械性操作：运行命令、读取输出、检查退出码。严格之处在于——绝不可以将失败解读为"应该没问题"——而非重度推理。重度语义推理属于 `review` skill。

> **范围**：SelfCheck 仅验证任务 `acceptance:` 块中指定的内容。它不对 spec 语义做交叉校验，不检查代码是否真正解决了用户层面的问题。这些是 `review` skill 的职责。

流程：

1. 运行任务 `acceptance:` 中的每一条命令
2. 捕获退出码 + 相关输出
3. 任一失败 → 不得声称 DONE
4. SelfCheck 范围严格等于 `acceptance:` —— 不多不少

### 📤 Report — 发出状态

触发：SelfCheck 之后，或在 BLOCKED / NEEDS_CONTEXT 时。

> **推理节奏**：🥐 **轻量**。按照固定的四状态机进行分类；不产生超出 SelfCheck 结果的新推理。

流程（定义参见 [references/state-machine.md](references/state-machine.md)）：

1. 分类为：DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED
2. 将状态行追加到任务文件的 `## Status log` 部分
3. 向用户发出结构化摘要，并建议下一个任务（不自动推进）
4. **若状态为 `DONE_WITH_CONCERNS` 或 `BLOCKED`**：发出一条 wiki 入库**建议**（绝不自动入库）——参见 [references/workflow.md#report-wiki-ingest-suggestion](references/workflow.md)。建议包含拟定的页面名称、类型，以及从关注点/阻塞点提炼的内容草稿。用户必须显式运行 `/sdd-kit:wiki` 才会入库。

## 四种状态

完整定义参见 [references/state-machine.md](references/state-machine.md)。速查：

| 状态 | 含义 |
|------|------|
| **DONE** | 所有验收命令通过，无已知妥协 |
| **DONE_WITH_CONCERNS** | 验收通过，但执行者发现了技术债务 / 妥协 / 非理想路径。必须记录关注点。 |
| **NEEDS_CONTEXT** | 存在歧义或信息缺失导致无法继续；执行者拒绝自行决定。必须说明需要什么上下文。 |
| **BLOCKED** | 环境 / 依赖 / 外部因素阻碍继续推进。必须指明阻塞因素。 |

## 目录结构

```
.claude/tasks/
└── <name>.tasks.md      # ← 状态日志追加在此文件内

.claude/impl-logs/       # 可选，首次长时间 impl 时创建
└── <name>.log.md        # 累积会话追踪（多任务运行）
```

## 状态行格式

精确格式，追加到任务文件的 `## Status log` 部分：

```
- [x] T-003 (DONE) — 2025-04-18 14:20 — all acceptance cmds green (3/3)
- [?] T-004 (DONE_WITH_CONCERNS) — 2025-04-18 14:50 — passed but: retry logic uses fixed 3 tries, no backoff; see note in src/webhooks/xhs-handler.ts:42
- [!] T-005 (NEEDS_CONTEXT) — 2025-04-18 15:10 — spec ambiguous on replay window: 24h vs 7d? acceptance doesn't specify
- [✗] T-006 (BLOCKED) — 2025-04-18 15:30 — db migration fails: local postgres 14 vs expected 15; need devops to align
```

勾选框语义：

- `[x]` — DONE
- `[?]` — DONE_WITH_CONCERNS
- `[!]` — NEEDS_CONTEXT
- `[✗]` — BLOCKED

## 核心规则

1. **禁止未经验证的声明** —— 绝不在未运行 `acceptance:` 命令的情况下发出 DONE。"应该可以工作" = NEEDS_CONTEXT，而非 DONE。
2. **禁止静默状态降级** —— BLOCKED 不会因为"我想到了变通方案"就变成 DONE。偏离验收标准的变通方案是 DONE_WITH_CONCERNS。满足验收标准的变通方案才是 DONE。
3. **禁止做设计决策，禁止自行研究** —— 若任务存在歧义（如含开放性动词 `校准 / 保持 / 验证`、缺少具体值、存在未解决的 `<TODO-DECIDE>`），发出 NEEDS_CONTEXT。不要自行编造选择。不要抓取外部文档、搜索网页或对比同类代码来填补空白——那是 spec / research 阶段的职责。将问题退回。
4. **禁止修改任务** —— impl 不编辑任务的标题、交付物或验收标准。仅追加状态日志。
5. **一次一个任务** —— 完成 + 报告后再选下一个。防止半完成状态。
6. **SelfCheck = 验收** —— 若验收标准写的是"通过测试 X"，你就运行 X。不要少跑（假 DONE）。不要多跑（范围蔓延、无关失败）。不要质疑 spec——如果 spec 本身看起来有问题，发出 NEEDS_CONTEXT 或留给 `review` 标记 SPEC_DRIFT。
7. **临时模式同样遵守以上规则** —— 即使没有任务文件，同样使用四状态报告。
8. **禁止自动推进到下一任务** —— impl 报告完一个任务即停止，除非用户明确说"继续"。

## 初始化

若 `.claude/tasks/` 不存在：impl 无法运行任务模式，仅支持临时模式。
若 `.claude/impl-logs/` 不存在且用户需要多会话追踪：首次 impl 时创建。

## 本 skill 不做的事

- 不修改 spec（spec 具有权威性；若 spec 有误，返回 NEEDS_CONTEXT，或留给 `review` 标记 SPEC_DRIFT）
- 不修改任务定义（仅追加状态）
- 不因"显而易见"而跳过 SelfCheck
- 不对 spec 进行语义审计（那是 `review` skill 的职责）
- 不将多个任务捆绑在一次提交 / 一条状态行中
- 不在 DONE 后自动推进——由用户决定
- 不自动调用 `review`——由用户决定何时审计

## 何时不激活

- 任务文件中有未解决的上游 BLOCKED 依赖——先解决依赖
- 用户仍在 research/spec 阶段——使用前置 skill
- 实际无需代码变更（纯设计讨论）——直接回答即可

## 反模式

参见 [references/anti-patterns.md](references/anti-patterns.md)。速查列表：

- 未运行 `acceptance:` 命令就声称 DONE
- 将 BLOCKED 合并到 DONE_WITH_CONCERNS 却不指明阻塞因素
- 悄悄做出设计选择来解除阻塞（应为 NEEDS_CONTEXT）
- 编辑任务的验收标准以使其通过
- "跑了测试"却不读输出
- 将无关的清理工作捆绑到任务提交中
- 在 SelfCheck 中对 spec 进行语义审计（属于 `review` 的职责）
