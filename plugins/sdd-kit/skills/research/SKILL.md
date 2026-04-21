---
name: research
description: "Index-first requirement exploration workspace for ambiguous needs before freezing them into spec. Produces `.claude/research/<topic>/` with `index.md`, append-only `log.md`, source-backed `raw/`, and topic notes under `notes/`. Encourages clarifying questions, supports multiple passes, and narrows understanding over time. Does NOT make final design decisions, write project policy, or auto-advance. Invoke only on explicit user request (e.g. '用 research skill 调研 <topic>')."
---

# Research — Index-first 需求探索工作区

在 `.claude/research/<topic>/` 下维护一个**带导航、可续写、带来源**的探索工作区。Research 的目标不是一次性收集资料，而是把模糊需求从**发散**逐步推进到“**足够收敛，值得进入 spec**”。

Research 采用 **index-first** 模式：

- `index.md` 是统一入口，供你或其他执行者冷启动时先读
- `log.md` 记录研究过程中的理解变化
- `raw/` 保留原始证据层
- `notes/` 记录主题化、带来源的解释与整理

## 在工作流中的定位

```text
[research] → spec → task → impl
    ↑
    └── 可在任何时候回到 research，继续补资料 / 提问 / 修正理解
```

Research 是**发散 → 收敛**阶段。它：

- 收集原始素材（代码、文档、URL、用户提供的材料）
- 通过提问和讨论帮助用户澄清需求
- 带来源地解释“这些事实对需求意味着什么”
- 将理解整理进可导航的 notes，而不是散落在聊天里
- 支持多轮进入、增量更新和 handoff
- **不做**最终设计决策
- **不自动**推进到 `spec`

当研究结果已经足够收敛、适合冻结时，才进入 `spec`。`spec` 负责**收敛 → 确定**，不是 research 第一次真正搞懂需求的地方。

## 六个原语

根据用户意图匹配对应原语；完整流程见 [references/workflow.md](references/workflow.md)。

### ❓ Clarify — 澄清问题与当前理解

触发词："调研 X"、"先搞清楚 X"、"这个需求到底应该怎么理解"、"我也不确定该怎么做，先看看"。

流程：

1. 暂定性重述需求：当前最可能的理解是什么
2. 列出已知、未知、待验证假设、潜在歧义
3. 必要时向用户提出 1-3 个最高杠杆的问题
4. 创建或更新 `index.md`，写入当前理解、当前研究范围、待澄清问题、意图锚定
5. 若理解发生显著变化，在 `log.md` 追加一条记录
6. 输出当前 framing，并决定继续 collect 还是继续 clarify

> 推理节奏：重度。Research 的价值不只是找资料，而是帮助用户把需求问题问对。

### 📥 Collect — 收集原始素材

触发词："收集 X 的资料"、"看一下代码里 X 怎么做的"，或用户粘贴 URL / 文档 / 截图 / 代码片段。

流程：

1. 接收原始输入（用户材料、代码片段、URL、截图）→ `raw/`
2. 扫描代码库中相关入口 → 提取最小化引用，保存为 `raw/codebase-<area>.md`
3. **用户提供的 URL = 强制获取**：穷尽工具阶梯，需要登录则暂停请求用户协助。按 [references/data-collection.md](references/data-collection.md) 执行。
4. 研究过程中发现的 URL：按当前理解和意图锚定判断是否追踪
5. 收集过程中若暴露出新的需求歧义、隐藏前提或互斥解释 → 回到 Clarify 或 Reframe
6. Collect 阶段不做重度提炼；原始素材保持低损、可回溯

### 📝 Note — 写主题化研究笔记

触发词："整理一下"、"把收集到的解释清楚"、"这些资料意味着什么"、"按主题整理"。

流程：

1. 阅读 `raw/*.md`，按**主题、发现、约束、歧义点**分组，而不是按来源分组
2. 针对每个独立主题写或更新 `notes/<subtopic>.md`
3. 每篇笔记包含：当前结论 / 来源 / 这对需求意味着什么 / 仍未解决的问题 / 相关笔记
4. 允许写出“哪种理解更受证据支持”“这条证据改变了什么判断”，但必须带来源
5. 若存在多种合理解释，明确并列写出；Research 可以比较，不可以拍板
6. 未贡献到任何 note 的 raw 文件保留，不删除

> 推理节奏：重度。Research 在这里把“信息”转成“可复用、可导航的理解”。

### ✅ Check — 收敛度与缺口检查

触发：整理出一批主题 notes 之后，或用户问"现在够不够进入 spec"。

流程：

1. 回答当前三个问题：
   - 现在已经明确了什么？
   - 还有哪些未解歧义真正会影响后续决策？
   - 当前是否足够收敛，可以进入 spec？
2. 将结论更新到 `index.md` 的 `## 当前是否适合进入 spec`
3. 若答案是“还不够” → 明确下一轮应做的是继续 Collect 还是继续 Clarify
4. 若答案是“已经足够” → 可将 `status` 置为 `ready-for-spec`，但不自动推进

### 📐 Reframe — 更新理解与研究边界

触发：探索过程中发现最初的问题提法不对、范围需要修正、或对需求的理解发生变化。

流程：

1. 更新 `index.md` 中的当前理解 / 当前研究范围 / 暂不纳入 / open questions
2. 在 `log.md` 追加一条变更记录，写明是什么证据或讨论改变了理解
3. 保留已有 `raw/` 与 `notes/` 文件；必要时在相关 note 中标注哪些内容已被新理解修正
4. 输出变更摘要：这次理解为什么改变、改变了什么、接下来补什么

### 📤 Snapshot — 刷新研究入口与状态

触发词："总结一下 research"、"先记一下当前状态"、"research 先暂停"、"这一轮先到这"、"可以结束研究了"。

流程：

1. 刷新 `index.md`：当前理解 / 主题导航 / 关键来源 / open questions / readiness
2. 在 `log.md` 追加本轮总结
3. 若后续大概率还会继续 → `status: open`
4. 若当前足够进入 spec → `status: ready-for-spec`
5. 若用户明确认可“本轮 research 已足够完成” → 可标记 `status: closed`
6. 输出状态摘要；**不调用** spec skill，也**不自动** ingest wiki

## 目录结构

```text
.claude/research/<topic>/
├── index.md                    # 统一入口：当前理解 / 导航 / open questions / readiness
├── log.md                      # 追加式研究日志：本轮做了什么、理解怎么变了
├── raw/                        # 原始证据层，低损清洗与格式规范化（不删除）
│   ├── codebase-<area>.md      # 来自代码的引用，含 file:line 引用
│   ├── ext-<source>.md         # 外部材料摘要
│   ├── ext-<source>-failed.md  # 获取失败的外部来源
│   └── user-input-YYYY-MM-DD.md
└── notes/                      # 主题化研究笔记：结论 / 来源 / 含义 / 未决问题
    ├── <subtopic-a>.md
    └── <subtopic-b>.md
```

`<topic>` 使用 kebab-case 命名，按话题命名（不使用日期）。示例：`.claude/research/xhs-customer-webhook/`。

## 核心规则

1. **Research 负责发散 → 收敛** —— 它帮助用户把问题问清楚、把理解收窄；最终冻结由 spec 完成。
2. **`index.md` 是 research 的统一入口** —— 其他执行者应先读它，而不是自己拼目录结构。
3. **`log.md` 记录理解变化** —— 重要的研究轮次、重构理解、状态切换应追加到日志中，而不是只留在聊天里。
4. **`raw/` 保持 raw** —— 允许低损清洗与格式归一化，但不写解释与决策。
5. **`notes/` 是带来源的解释层** —— 它可以写“这对需求意味着什么”“目前更支持哪种理解”，但必须引用 `raw/`。
6. **允许提问并鼓励提问** —— 当不问问题就无法决定该收集什么时，应先 Clarify，而不是机械继续 Collect。
7. **未解歧义是一等公民** —— 不要急着把一切都写成确定句；把真正影响后续决策的不确定性显式写进 `index.md` 与相关 notes。
8. **用户提供的 URL 是强制性的** —— 穷尽工具阶梯，需要登录则暂停请求用户协助，不可静默跳过。
9. **Research 支持多轮进入与增量更新** —— `status: open` 是正常状态；已有工作区可以继续追加，不必重开。
10. **不删除 raw 文件** —— 旧 raw/ 作为审计链与后续研究素材保留。理解改变时，更新导航与解释，不清空证据。
11. **不做最终设计决策** —— Research 可以比较、解释、指出哪种理解更受证据支持；不能写“我们最终选择 X”。
12. **不自动推进、不自动入库** —— 研究入口和日志更新后停止。是否进入 spec 或 wiki 由用户决定。
13. **项目策略不属于 research** —— TDD、强制测试、固定 acceptance、团队流程等项目策略属于 `CLAUDE.md` / rules，而非 research skill。
14. **Research 借用 wiki 的导航方式，不复制 wiki 的治理体系** —— 使用 index-first 导航，但不引入 root page / page taxonomy / 长期知识治理。

## 初始化

若 `.claude/research/` 不存在，首次使用时静默创建。

每次新研究，创建 `.claude/research/<topic>/` 并输出：

```text
📁 .claude/research/<topic>/ 已创建
   当前理解: <provisional understanding>
   待澄清: <top ambiguities>
   下一步: clarify / collect / note
```

若研究目录已存在且 `index.md` 仍为 `status: open | ready-for-spec`，优先继续该工作区，而不是重建。

## 本 skill 不做的事

- 不冻结方案 / 不做最终设计选择（使用 `spec` skill）
- 不拆任务或写代码（使用 `task` / `impl` skill）
- 不自动将发现摄取到 wiki（由用户通过 `wiki` skill 触发）
- 不把项目策略写成 research 规则（这些属于 `CLAUDE.md` / rules）
- 不要求固定线性流程 —— Research 可回环，但必须保持 index-first 的结构化记录

## 何时不激活

- 用户已有清晰 spec 并要求产出任务 → 使用 `task` skill
- 用户的问题是无需建立研究工作区即可直接回答的单一事实问答 → 直接回答
- 用户正在 impl 中途询问局部代码解释 → 内联回答，不必开启 research 目录
- 已存在仍有效的 research 工作区 → 直接读取并继续，不重做

## 反模式（请勿这样做）

详见 [references/anti-patterns.md](references/anti-patterns.md)。快速清单：

- 把 research 当成纯资料仓库，只收集不解释
- 没有 `index.md` 导航，逼后续执行者自己重建上下文
- 把所有歧义机械推给 spec，不在 research 中先澄清
- 在 `notes/` 中偷运最终决策
- 在 research 中写入 TDD / 测试先行 / 强制 acceptance 等项目策略
- 自动推进到 spec 或自动入库 wiki
- 静默跳过用户提供的 URL
- 删除 raw 文件或覆盖旧理解而不保留变更痕迹
