---
name: research
description: "Index-first requirement exploration workspace for ambiguous needs before freezing them into a package-local PRD via brainstorm. Produces `.arbor/research/<topic>/` with `index.md`, append-only `log.md`, source-backed `raw/`, and topic notes under `notes/`. Encourages clarifying questions, supports multiple passes, and narrows understanding over time. Does NOT make final design decisions, write project policy, or auto-advance. Invoke only on explicit user request (e.g. '用 research skill 调研 <topic>')."
---

# Research — Index-first 需求探索工作区

在 `.arbor/research/<topic>/` 下维护一个**带导航、可续写、带来源**的探索工作区。Research 的目标不是一次性收集资料，而是把模糊需求从**发散**逐步推进到“**足够收敛，值得进入 brainstorm 并写入 `.arbor/tasks/<name>/prd.md`**”。

Research 采用 **index-first** 模式：

- `index.md` 是统一入口，供你或其他执行者冷启动时先读
- `log.md` 记录研究过程中的理解变化
- `raw/` 保留原始证据层
- `notes/` 记录主题化、带来源的解释与整理

## 在工作流中的定位

```text
[research] → brainstorm → impl → review
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

当研究结果已经足够收敛、适合冻结时，才进入 `brainstorm`。`brainstorm` 负责**需求澄清定稿与 design framing**：形成 executable package PRD（`.arbor/tasks/<package>/prd.md`），并在 PRD 内写好 ordered `## Slices`。`ready-for-brainstorm` 只表示已有材料足够让 brainstorm 接手，不表示需求已经冻结；后续 brainstorm 仍应区分 research 支持的事实、候选方向和未由用户确认的范围 / 验收假设，并按需询问 `normal` / `grill-me` 模式。

## 六个原语

### ❓ Clarify — 澄清问题与当前理解

流程：
1. 暂定性重述需求，并先判断原始提法背后更像用户痛点、工作流问题、技术约束、采用阻力还是方案假设
2. 将模糊需求改写成 research question；适合时补一条 `How might we ...` 式机会问题
3. 列出已知、未知、候选理解、潜在歧义；只暴露待澄清点，不做假设分级或最终取舍
4. 必要时提出 1-3 个最高杠杆问题，优先询问会影响 downstream brainstorm 的问题
5. 更新 `index.md`
6. 若理解显著变化，在 `log.md` 追加记录
7. 输出当前 framing，并决定继续 collect 还是继续 clarify

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
1. 回答四个问题：
   - 现在已经明确了什么？
   - 有哪些候选理解仍然并存？
   - 还有哪些未解歧义会影响 brainstorm 开始有效澄清？
   - 当前资料是否足够让 brainstorm 接手继续收敛？
2. 检查 `当前范围 / 暂不纳入` 是否有理由，避免 research 扩散
3. 将结论更新到 `index.md` 的 `## 当前是否适合进入 brainstorm`
4. 若答案是“还不够” → 明确下一轮应做的是继续 Collect 还是继续 Clarify
5. 若答案是“已经足够” → 可将 `status` 置为 `ready-for-brainstorm`，但不自动推进

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
7. 若本轮 research 收集了有长期复用价值的外部知识（第三方 API 接口/地址/认证流程、平台限制、外部系统行为等），提醒用户是否需要用 wiki skill 将关键接口、地址和约束沉淀为 wiki 页面（type: source / entity），带上原始获取源以便后续更新验证

## Subagent fan-out（可选）

Research 可以在 Collect 阶段使用 subagent 做并行资料收集、代码扫描或竞争性假设调查，但它不是默认路径。

只有当 research intent 已经明确，且调查可以拆成多个互不依赖的分支时，才使用 subagent。若问题仍处于需求澄清阶段，或需要连续重构理解，优先由主会话直接推进 Clarify / Reframe。

subagent 只返回 source-backed packet，不直接写 `.arbor/research/<topic>/`，不判断 readiness，不做最终设计决策。主 research 会话必须审计 packet 的来源、相关性、遗漏和冲突，再决定是否写入 `raw/` / `notes/` / `index.md` / `log.md`。

使用目标是隔离 noisy exploration、扩大覆盖面，而不是引入新的 runtime 编排。若 fan-out 带来的整合成本高于信息收益，应避免使用。

推荐 packet：

```text
## Scope
## Sources checked
## Findings
## What this means for the requirement
## Open questions
## Confidence / gaps
## Suggested raw/note placement
```

## 核心规则

1. **Research 负责发散 → 收敛** —— 它帮助用户把问题问清楚、把理解收窄；最终冻结由 brainstorm 完成。
2. **先 framing 再 collect** —— 模糊需求先转成 research question / HMW / 候选理解，再决定搜什么。
3. **Research 提出候选理解，不审计假设** —— assumption 分级、方向取舍和 PRD/package 前风险判断属于 brainstorm。
4. **`index.md` 是 research 的统一入口**。
5. **`log.md` 记录理解变化**。
6. **`raw/` 保持 raw** —— 不写解释与决策。
7. **`notes/` 是带来源的解释层**。
8. **允许提问并鼓励提问**。
9. **未解歧义是一等公民**。
10. **暂不纳入要写原因** —— exclusions 是防止 research 扩散的工具。
11. **用户提供的 URL 是强制性的**。
12. **Research 支持多轮进入与增量更新**。
13. **不删除 raw 文件**。
14. **不做最终设计决策**。
15. **不自动推进、不自动入库**。
16. **项目策略不属于 research**。
17. **Research 借用 wiki 的导航方式，不复制 wiki 的治理体系**。

## 本 skill 不做的事

- 不冻结方案 / 不做最终设计选择（使用 `brainstorm` skill）
- 不拆执行计划或写代码（使用 `brainstorm` / `impl` skill）
- 不自动将发现摄取到 wiki（由用户通过 `wiki` skill 触发）
- 不把项目策略写成 research 规则

## 何时不激活

- 用户已有清晰需求并要求冻结执行范围 → 使用 `brainstorm` skill finalize package PRD
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
