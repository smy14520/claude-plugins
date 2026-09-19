---
name: domain-modeling
description: "Domain modeling and concept boundary sharpening. Use when clarifying domain terms, resolving overloaded words, defining business entities, or recording ADR decisions."
---

# Domain Modeling — 领域语言建模与概念消歧

消除人机协作与跨模块通信中的“词汇污染与概念歧义”，将隐性的业务领域术语、实体边界与核心架构决策显性化，纳入三级记忆体系。

## 触发时机（When to Invoke）

模型在以下具体节点自主激活本素养：
- **时机 A：访谈或代码中出现概念冲突或一词多义时**：例如发现团队与代码里混用 User / Account / Member，或草稿与未生效状态边界模糊，立即调用本技能消歧并录入 `.forge/wiki/concept/` 或 `entity/`；
- **时机 B：拍定不可逆架构决策（One-way Doors）时**：技术选型发生重大分叉（如改用内嵌 DB、引入消息队列），调用本技能沉淀轻量 ADR，详述理由与被否决备选路径的代价；
- **时机 C：提炼出不可逾越的领域铁律时**：提炼出高频、防犯错的硬性业务纪律（如“退款金额绝不可大于支付原额”），调用本技能起草提议写入 `.claude/rules/<domain>.md`。

## 维护资产与归宿

1. **核心实体与概念定义（存入 `.forge/wiki/concept/` 或 `entity/`）**：
   - 每一个业务概念一个单独页面；
   - 显式给出定义的英文名、中文含义、所属边界与反例；
   - 彻底消除一词多义（如明确区分“登录凭据”、“用户账户”与“资金账户”）。
2. **架构决策记录（存入 `.forge/wiki/decision/` 或 `docs/adr/`）**：
   - 记录不可逆架构决策（One-way doors）的技术推导与被否决备选路径的实证代价；
   - 格式：Status / Context / Decision / Consequences。
3. **不可逾越的领域硬规则（通过 `wiki` 提议写入 `.claude/rules/<domain>.md`）**：
   - 提炼出的高频防犯错硬性业务纪律，经人类确认后写入 rules。

## 执行准则（Discipline）

1. **先查后增**：在代码编写和访谈中，凡遇到新业务名词，先扫描 Wiki 索引，避免同一概念发明两个变量名或造成语义漂移；
2. **主动磨刀**：当访谈或重构拍定了一个核心业务实体的精准含义，立即形成结构化页面存入 `.forge/wiki/`；
3. **零实现细节**：概念与实体页只放定义、边界与反例，绝不堆砌单文件代码实现，代码实现细节让代码自己回答；
4. **Completion criterion**：在对话中展示已定义的概念或 ADR 决策摘要。

## 反模式（Anti-Patterns）

- **Dictionary Bloat**：把每个临时变量或单文件局部 helper 都当成领域实体来定义。
- **Silent Semantic Drift**：同一个业务词汇在不同模块被赋予完全不同的语义，未及时拆分概念。
- **Implementation Bleed**：在概念定义文档中粘贴大量易变的代码逻辑，导致文档迅速失效腐烂。
