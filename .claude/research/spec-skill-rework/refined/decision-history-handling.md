---
finding-type: precedent
confidence: high
date: 2026-04-21
---

<!-- 输出语言: 中文 -->

# 决策史处理:KEP/RFC 保留 vs sdd-kit 拆分

## 发现内容

"spec 是否保留决策过程 / 备选方案"是本次研究里 sdd-kit 与业界**最大的哲学分歧**。两种策略都有成熟先例,值得明确选择并坚持。

### 策略 A:合并保留(KEP / Rust RFC)

**KEP** 有独立 `## Alternatives` 和 `## Drawbacks` 章节,并在 `Implementation History` 里记录重大决策节点。

```markdown
## Drawbacks
<!-- Why should this KEP _not_ be implemented? -->

## Alternatives
<!--
What other approaches did you consider, and why did you rule them out?
These do not need to be as detailed as the proposal, but should include enough
information to express the idea and why it was not acceptable.
-->

## Implementation History
<!-- - the date implementation started
     - the version of Kubernetes where the KEP graduated to GA
     - when the KEP was retired or superseded -->
```

**Rust RFC** 合并为 `## Rationale and alternatives` + 独立 `## Prior art` + `## Unresolved questions`。RFC 是**决策过程**文档,不是定稿契约,保留备选方案是其核心价值。

**适用前提**:
- spec 即决策记录(KEP/RFC 面向社区审议,"为什么这样选"本身就是 spec 的价值)
- 读者群体多元(reviewer 需要理解决策过程,implementer 只看 Design Details)
- 变更频率低(一份 RFC 定稿后多年不变,决策史是重要历史资料)

### 策略 B:拆分(sdd-kit / SpecKit)

**sdd-kit** 把 spec 限定为"最终契约",禁止决策过程,决策史推到 `[[decision-*]]` wiki 页:

```
- "We considered HMAC vs RSA and chose HMAC because..." →
  应写入 [[decision-hmac-vs-rsa-for-webhook]] wiki 页面
```

**SpecKit** 没有 Alternatives 章节,但有 Assumptions 章节明确写"基于什么默认选择"。决策过程由 `/speckit.clarify` 命令在生成 spec 前完成,答案合并进 spec 不保留过程。

**适用前提**:
- spec 面向高频迭代(AI agent 每个 feature 都写一份新 spec)
- 读者主要是 **task/impl 执行者**(只想知道要做什么,不关心为什么选这个方案)
- 有独立的决策存档机制(wiki decision 页 / ADR / clarification 记录)

### 两者对比

| 维度 | 策略 A(合并保留) | 策略 B(拆分) |
|------|------------------|---------------|
| 单文件信息密度 | 低(含过程 + 结论) | 高(只含结论) |
| 单文件可读时间 | 慢 | 快 |
| 决策可追溯 | 在 spec 内(单文件) | 需跳到 wiki(多文件) |
| 变更维护成本 | 高(改决策要更新 Alternatives) | 低(wiki decision 页独立演化) |
| 适合的团队 | 社区审议 / 开源标准 | 内部快迭代 / AI agent 驱动 |
| 是否禁止"我们考虑过 X" | 否,鼓励 | 是 |

## 来源

- `raw/ext-kubernetes-kep-template.md` Drawbacks + Alternatives + Implementation History 段
- `raw/ext-rust-rfc-template.md` Rationale and alternatives + Prior art + Unresolved questions 段
- `raw/ext-github-speckit-spec-template.md` Assumptions 段
- `plugins/sdd-kit/skills/spec/references/content-contract.md` 第 102-135 行(禁止章节列表)
- `plugins/sdd-kit/skills/spec/references/anti-patterns.md` #1 #2 #3 #7 #11

## 意义

### 确认 sdd-kit 选择策略 B(拆分)

sdd-kit 的定位是"AI agent 驱动的高频迭代工程 spec",目标读者是 task/impl 的执行者,这些条件都指向策略 B。改造时**应坚持**这个决定,不要被 KEP/RFC 的 Alternatives 章节吸引去摇摆。

### 但应从 KEP/RFC 借鉴两点

1. **Risks / Mitigations(KEP)**:策略 B 不保留决策过程,但**识别过的风险**仍值得留在 spec 里,供 task/impl 阶段防御性编码。建议改造时新增**可选的** Risks 章节(不是 Alternatives)。

2. **Unresolved questions(Rust RFC)的"承认 + 显式列出"精神**:sdd-kit 当前策略是"Finalize 前必须清空所有 TODO-DECIDE",强制决策。但现实中有些问题必须到 impl 时才能决(如性能调优参数)。可以考虑**保留显式的"已知延迟决策项"章节**,用结构区分"必须 spec 阶段决"和"可以 impl 阶段决",避免把模糊未决项强行塞进 spec。

   当前 sdd-kit 的处理方式是:impl 遇到未决 → NEEDS_CONTEXT 退回 spec。这其实是**隐式**的未决机制。显式化它可以降低误发 NEEDS_CONTEXT 的概率。

### 需要保持的边界

- Decision wiki 页(`[[decision-*]]`)**必须存在且可被 spec 链接**。这要求 wiki skill 已经稳定(现状:wiki skill 已完成,OK)。
- 不能让 spec 里的 Risks 章节变成 Alternatives 伪装 —— Risks 说的是"已识别的威胁",不是"考虑过的方案"。改造时要在 content-contract 里明确区分。

## 待确认问题

- Risks/Mitigations 作为可选章节,用什么 `*(optional)*` 标签?还是用 "无则删除本节"的模式(现有 Background 章节的做法)?
- "显式未决项"章节是否值得加?取舍:加 = 承认现实,不加 = 保持"spec 即决策完成态"的纯粹。我倾向**不加**,让 impl 的 NEEDS_CONTEXT + `<TODO-DECIDE>` 继续承担,避免 spec 再分化
