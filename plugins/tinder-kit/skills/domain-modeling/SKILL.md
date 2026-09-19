---
name: domain-modeling
description: "Domain modeling and project glossary maintenance. Use when clarifying domain terms, resolving overloaded words, recording ADRs, or updating CONTEXT.md."
---

# Domain Modeling — 领域语言建模与架构沉淀

消除团队与 AI 协作中的“词汇污染与概念歧义”，将隐性的业务术语与核心实体显性化，维护活在项目主干的全局全景文档。

## 维护资产

1. **项目根目录 `CONTEXT.md`（活字典）**：
   - **核心实体与词汇表**：定义每个业务实体的准确英文名与中文含义，消除一词多义；
   - **系统级核心接缝（Architectural Seams）**：记录系统中已稳定的最顶层深接口；
   - **设计禁忌与原则**：不可逾越的业务约束。
   - *排斥项*：严禁在 `CONTEXT.md` 堆砌函数实现细节、配置清单或临时变更日志，保持极高信噪比。
2. **架构决策记录（`docs/adr/NNNN-<slug>.md`）**：
   - 记录每一个“为什么采用方案 A 而非方案 B”的不可逆架构抉择；
   - 格式：Status / Context / Decision / Consequences。

## 执行准则（Discipline）

1. **先查后增**：在代码编写和需求访谈中，凡遇到新名词，先对照 `CONTEXT.md`，避免同一概念发明两个变量名；
2. **主动磨刀**：当访谈或重构拍定了一个核心名词的精准含义，立即就地更新 `CONTEXT.md`；
3. **双向流动**：`CONTEXT.md` 作为全景输入注入给每一个编码和审查子 Agent，确保整个系统的所有参与者使用同一种方言说话；
4. **Completion criterion**：`CONTEXT.md` 或 `docs/adr/` 已写入并呈现更新 Diff。

## 反模式（Anti-Patterns）

- **Dictionary Bloat**：把每个临时变量或辅助函数都塞进 `CONTEXT.md`，使其沦为代码注释堆砌场。
- **Silent Semantic Drift**：同一个业务词汇在不同模块被赋予完全不同的语义（如 Account 同时代表登录凭据与银行账户），却未在词汇表中拆分。
