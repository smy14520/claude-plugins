---
name: research
description: "Index-first requirement exploration workspace for ambiguous needs before freezing them into brainstorm. Produces `.claude/research/<topic>/` with `index.md`, append-only `log.md`, source-backed `raw/`, and topic notes under `notes/`. Encourages clarifying questions, supports multiple passes, and narrows understanding over time. Does NOT make final design decisions, write project policy, or auto-advance. Invoke only on explicit user request (e.g. '用 research skill 调研 <topic>')."
---

# Research — Index-first 需求探索工作区

在 `.claude/research/<topic>/` 下维护一个**带导航、可续写、带来源**的探索工作区。Research 的目标不是一次性收集资料，而是把模糊需求从**发散**逐步推进到“**足够收敛，值得进入 brainstorm**”。

Research 采用 **index-first** 模式：

- `index.md` 是统一入口，供你或其他执行者冷启动时先读
- `log.md` 记录研究过程中的理解变化
- `raw/` 保留原始证据层
- `notes/` 记录主题化、带来源的解释与整理

## 在工作流中的定位

```text
[research] → brainstorm → task → impl
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
- **不自动**推进到 `brainstorm`

当研究结果已经足够收敛、适合冻结时，才进入 `brainstorm`。`brainstorm` 负责**收敛 → 形成可拆解 PRD/context artifact**，不是 research 第一次真正搞懂需求的地方。

## 六个原语

### ❓ Clarify — 澄清问题与当前理解

流程：
1. 暂定性重述需求
2. 列出已知、未知、待验证假设、潜在歧义
3. 必要时提出 1-3 个最高杠杆问题
4. 更新 `index.md`
5. 若理解显著变化，在 `log.md` 追加记录
6. 输出当前 framing，并决定继续 collect 还是继续 clarify

### 📥 Collect — 收集原始素材

流程：
1. 接收原始输入 → `raw/`
2. 扫描代码库相关入口 → `raw/codebase-<area>.md`
3. 用户提供的 URL 强制获取，必要时请求登录协助
4. 研究中发现的 URL 按意图锚定判断是否追踪
5. 新的隐藏前提 / 互斥解释出现时，回到 Clarify 或 Reframe
6. 保持原始素材低损、可回溯

### 📝 Note — 写主题化研究笔记

流程：
1. 阅读 `raw/*.md`，按主题 / 发现 / 约束 / 歧义点分组
2. 针对每个主题写或更新 `notes/<subtopic>.md`
3. 每篇笔记包含：当前结论 / 来源 / 这对需求意味着什么 / 仍未解决的问题 / 相关笔记
4. 允许比较解释，不允许最终拍板
5. 未贡献到 note 的 raw 文件保留，不删除

### ✅ Check — 收敛度与缺口检查

触发：整理出一批主题 notes 之后，或用户问"现在够不够进入 brainstorm"。

流程：
1. 回答三个问题：
   - 现在已经明确了什么？
   - 还有哪些未解歧义真正会影响后续 task/impl？
   - 当前是否足够收敛，可以进入 brainstorm？
2. 将结论更新到 `index.md` 的 `## 当前是否适合进入 brainstorm`
3. 若答案是“还不够” → 明确下一轮应做的是继续 Collect 还是继续 Clarify
4. 若答案是“已经足够” → 可将 `status` 置为 `ready-for-brainstorm`，但不自动推进

### 📐 Reframe — 更新理解与研究边界

流程：
1. 更新 `index.md` 中的当前理解 / 当前研究范围 / 暂不纳入 / open questions
2. 在 `log.md` 追加一条变更记录
3. 保留已有 `raw/` 与 `notes/` 文件；必要时标注哪些内容已被新理解修正
4. 输出变更摘要

### 📤 Snapshot — 刷新研究入口与状态

流程：
1. 刷新 `index.md`：当前理解 / 主题导航 / 关键来源 / open questions / readiness
2. 在 `log.md` 追加本轮总结
3. 若后续大概率还会继续 → `status: open`
4. 若当前足够进入 brainstorm → `status: ready-for-brainstorm`
5. 若用户明确认可本轮 research 已足够完成 → `status: closed`
6. 输出状态摘要；**不调用** brainstorm skill，也**不自动** ingest wiki

## 核心规则

1. **Research 负责发散 → 收敛** —— 它帮助用户把问题问清楚、把理解收窄；最终冻结由 brainstorm 完成。
2. **`index.md` 是 research 的统一入口**。
3. **`log.md` 记录理解变化**。
4. **`raw/` 保持 raw** —— 不写解释与决策。
5. **`notes/` 是带来源的解释层**。
6. **允许提问并鼓励提问**。
7. **未解歧义是一等公民**。
8. **用户提供的 URL 是强制性的**。
9. **Research 支持多轮进入与增量更新**。
10. **不删除 raw 文件**。
11. **不做最终设计决策**。
12. **不自动推进、不自动入库**。
13. **项目策略不属于 research**。
14. **Research 借用 wiki 的导航方式，不复制 wiki 的治理体系**。

## 本 skill 不做的事

- 不冻结方案 / 不做最终设计选择（使用 `brainstorm` skill）
- 不拆任务或写代码（使用 `task` / `impl` skill）
- 不自动将发现摄取到 wiki（由用户通过 `wiki` skill 触发）
- 不把项目策略写成 research 规则

## 何时不激活

- 用户已有清晰 brainstorm 并要求产出任务 → 使用 `task` skill
- 用户的问题是无需建立研究工作区即可直接回答的单一事实问答 → 直接回答
- 用户正在 impl 中途询问局部代码解释 → 内联回答
- 已存在仍有效的 research 工作区 → 直接读取并继续

## 反模式（请勿这样做）

- 把 research 当成纯资料仓库，只收集不解释
- 没有 `index.md` 导航，逼后续执行者自己重建上下文
- 把所有歧义机械推给 brainstorm，不在 research 中先澄清
- 在 `notes/` 中偷运最终决策
- 自动推进到 brainstorm 或自动入库 wiki
- 静默跳过用户提供的 URL
- 删除 raw 文件或覆盖旧理解而不保留变更痕迹
