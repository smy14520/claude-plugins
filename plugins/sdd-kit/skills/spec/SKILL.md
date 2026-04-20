---
name: spec
description: "Produce a dependable single-file implementation spec for a feature or change. Output: `.claude/specs/<name>.md` — a contract covering goal, non-goals, interface, constraints, data/state, integration, test strategy. Strictly excludes decision history, rejected alternatives, and discovery narrative. Task skill consumes it; impl executes against it. Does NOT auto-advance. Invoke only on explicit user request (e.g. '用 spec skill 写 <name>')."
---

# Spec — 可靠的设计契约

生成一个单文件规格说明，输出至 `.claude/specs/<name>.md`。task skill 可据此分解任务，impl skill 可据此执行实现，无需重新做任何决策。

## 在四阶段工作流中的定位

```
research → [spec] → task → impl
            ↓
            └─── 可引用 wiki 中的已有经验（只读，需用户引导）
```

Spec 是**决策关卡**。未决问题到此为止，模糊歧义到此为止。spec 之后的下游阶段是执行，而非探索。

- **输入**：用户意图 + 可选的 research `findings.md` + 可选的 wiki 上下文（需用户引导查询）
- **输出**：一个 `.claude/specs/<name>.md`
- **禁止项**：决策历史、被否决的备选方案、探索过程叙述（它们应归入 `[[decision-xxx]]` wiki 页面，不属于这里）

## 三个原语

根据用户意图匹配对应原语；完整流程参见 [references/workflow.md](references/workflow.md)。

### 🎯 Frame — 目标、非目标、约束

触发语："开始写 spec X"、"spec 一下 X"、"定方案 X"。

> **推理节奏**：🍞 **重度**。Frame 阶段设定的是所有下游工作的不可变前提——如有扩展思考 / "think harder" 功能，应启用。此处的疏忽会层层放大。

流程（详见 `references/workflow.md#frame`）：

1. 命名 spec（kebab-case，按主题命名，不使用日期）
2. 若存在 `.claude/research/<topic>/findings.md` 且用户引用了它，则读取
3. 确立：目标（一句话）/ 非目标（至少 2 条）/ 硬约束
4. 从 [assets/templates/spec.md](assets/templates/spec.md) 模板生成骨架 `spec.md`

### ⚖️ Decide — 解决未决问题

触发语：起草过程中，spec 中出现未解决的 `<TODO-DECIDE: ...>` 标记时。

> **推理节奏**：🍞 **重度**。此处的每项决策都是 task + impl 的冻结前提。启用扩展思考，不要急。

流程：

1. 列举所有未决问题（来自 research 或新浮现的）
2. 逐一向用户展示选项，由用户选择（每个决策单独一轮交互，不批量打包）
3. 将每项已确认的选择**以平铺陈述的形式**记入 spec
4. 若用户希望保留决策依据，主动提议："要不要把这个决策的来龙去脉 ingest 为 `[[decision-<name>]]` wiki 页面？spec 本身不保留决策史。"
5. 不得将被否决的备选方案写入 spec

### ✅ Finalize — 封定 spec

触发语："spec 定稿"、"finalize the spec"、用户确认所有未决问题已解决。

> **推理节奏**：🥐 **轻度**。机械性的内容契约检查，无需扩展思考。

流程：

1. 扫描 spec 中剩余的 `<TODO-DECIDE>` 或 `<TBD>` — 必须为零
2. 执行内容契约检查（见 `references/content-contract.md`）：
   - 无决策叙述
   - 不列出备选方案
   - 无过程记录（"我们先想到……后来意识到……"）
3. 设置 frontmatter `status: accepted`、`date: today`
4. 输出结稿摘要，并指向下一步（task skill 或直接 impl）
5. 不自动调用 task skill

## 目录结构

```
.claude/specs/
├── <feature-a>.md      # 每个功能/变更一个 spec，按主题命名
├── <feature-b>.md
└── archive/            # 可选，用于存放已废弃的 spec
    └── <feature-a>-v1.md
```

命名规则：

- kebab-case 主题名，不含日期，不加版本后缀
- 通过 frontmatter `status: superseded` 进行版本管理，必要时移入 `archive/`

## 核心规则

1. **一个 spec = 一份契约** — 一个 spec 描述一个功能或变更。多功能 spec 必须拆分。
2. **不含决策历史** — spec 是"我们将构建什么"，而非"我们如何走到这里"。决策历史存放在 `[[decision-xxx]]` wiki 页面中，需显式 ingest。
3. **不列出备选方案** — 如果读者需要了解曾考虑过的方案，那是决策页面的职责，不是 spec 的职责。
4. **执行者可直接上手** — task/impl 工程师阅读此 spec 后应无需任何额外上下文即可行动。若仍需重新决策，说明 spec 存在未解决的决策。
5. **约束必须显式声明** — 速率限制、SLO、不变量、安全属性：直接写明，不以引用代替。
6. **Wikilink 是可选的辅助** — spec 可以链接到 `[[entity-xxx]]` 或 `[[concept-xxx]]` 提供背景，但不得依赖 wiki 的存在。Wikilink 是读者辅助手段，不是依赖项。
7. **不自动推进** — 定稿后，skill 停止。task skill 需单独调用。

## 初始化

若 `.claude/specs/` 不存在，首次使用时静默创建。

每个 spec：从 [assets/templates/spec.md](assets/templates/spec.md) 模板创建 `.claude/specs/<name>.md`。

## 本 skill 不做什么

- 不采集新的原始素材 — 使用 `research` 完成
- 不分解为任务 — 使用 `task` 完成
- 不编写代码 — 使用 `impl` 完成
- 不自动读取/合并 research — 用户须显式引用（`"基于 research findings 写 spec"`）
- 不向 wiki ingest 任何内容 — ingest 须通过 `wiki` skill 显式执行

## 何时不应激活

- 用户问的是直接实现问题（简单变更不需要 spec）
- 用户仍在探索方案（先使用 `research`）
- 用户已进入 impl 阶段并在调整方向（spec 增补可以；但在飞行中途创建新 spec 可能过度工程化）

## 反模式

参见 [references/anti-patterns.md](references/anti-patterns.md)。快速列表：

- 保留被否决的备选方案"以供参考"
- 将 spec 写成决策叙述（"我们首先考虑了 X，然后考虑了 Y，最终选择了 Z"）
- 将多个功能拼在一个 spec 中
- 在已接受的 spec 中遗留 `<TODO-DECIDE>` 标记
- 结尾时自动触发 task skill
- 将约束写成模糊目标（"应该快"）而非具体数字的 SLO
