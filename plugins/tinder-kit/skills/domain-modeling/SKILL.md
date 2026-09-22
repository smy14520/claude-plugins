---
name: domain-modeling
description: "构建并打磨项目的领域模型与统一语言。在统一多义业务名词、界定实体边界、人机对账老代码、或按严格三门槛记录 ADR 架构决策时调用。"
---

# Domain Modeling — 领域建模与统一语言

在系统设计与重构中，主动构建并严密打磨项目的领域模型（Domain Model）。这是一项**主动的、带有攻击性的工程素养（Active Discipline）**：随时挑战模糊术语、发明边缘场景压测概念边界、与老代码进行真实性对账，并在概念成形的当下即时沉淀。

---

## 核心执行操典（Active In-Session Discipline）

### 1. 对照词典主动挑战（Challenge against the glossary）
当对话或新需求中使用的术语与既有概念（`CONTEXT.md` 或 `.forge/wiki/concept/`）发生冲突或语义漂移时，立即指出并纠偏：
> *"在项目词典中 'Cancellation' 仅指未发货前的取消，但你刚才的表述似乎包含了已发货退款——到底以哪个为准？"*

### 2. 锐化模糊与过载词汇（Sharpen fuzzy language）
当出现一词多义或模糊不清的词汇时，强制提出精准的规范名词进行消歧：
> *"你刚才说了 'Account'——你是指计费维度的 Customer（结算账户），还是鉴权维度的 User（登录账号）？这是两个完全不同的实体。"*

### 3. 用具体场景压力测试概念边界（Discuss concrete scenarios）
讨论实体关系时，**主动发明能够探测边缘 Case 的真实场景**，迫使精确定义概念的边界：
> *"如果一个拼团订单中有 1 件缺货，此时该订单属于 PARTIAL_PAID 还是 FAILED？未成团的定金退不退？"*

### 4. 严密的人机代码对账（Cross-reference with code）
**这是最关键的防幻觉动作！** 当人类描述某项业务流程时，Agent 必须主动翻阅现有代码库求证是否一致。一旦发现矛盾，当场指出：
> *"你的描述中提到订单支持部分退款，但我检索了当前 `OrderService.ts` 中的实现，发现里面直接全量作废整笔订单并抛出不可拆分异常——代码与你的设想矛盾，哪一个才是存量真相？"*

### 5. 即时就地更新（Update inline）
一旦某个概念的定义达成共识，立即更新至 `CONTEXT.md` 或 `.forge/wiki/concept/<slug>.md`。**严禁批量攒到最后**，随着概念出现随时捕获。
- 格式规范见 [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md)；
- `CONTEXT.md` 是纯粹的业务概念字典，严禁写入具体技术实现细节或代码片段。

### 6. 克制地提出 ADR 提案（Offer ADRs sparingly）
坚决反对低价值 ADR 泛滥。只有以下**三项条件全部满足时**，才提出记录 ADR：
1. **Hard to reverse（难以逆转）**：日后推翻决定的技术或业务代价极其高昂（One-way door 决策）；
2. **Surprising without context（无上下文时反直觉）**：未来读者看到代码会极其困惑：“为什么当时要这么怪异地实现？”；
3. **The result of a real trade-off（真实取舍的产物）**：确实存在另一个切实可行的备选方案，而我们基于具体理由放弃了它。

缺少任一项，坚决跳过 ADR。模板与规范见 [ADR-FORMAT.md](./ADR-FORMAT.md)。
