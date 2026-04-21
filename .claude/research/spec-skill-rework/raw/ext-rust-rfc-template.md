---
url: https://raw.githubusercontent.com/rust-lang/rfcs/master/0000-template.md
tool: read_url_content
fetched_at: 2026-04-21 21:30
---

# Rust RFC 模板(完整清洗)

> 原文为 rust-lang/rfcs 的 0000-template.md,是社区提议新特性的标准模板。结构紧凑,注释指引精简。

---

## 顶层结构(H2 依序)

```
## Summary
## Motivation
## Guide-level explanation
## Reference-level explanation
## Drawbacks
## Rationale and alternatives
## Prior art
## Unresolved questions
## Future possibilities
```

注意:**无 Goals / Non-Goals 章节**。Rust RFC 的"范围边界"由 Motivation 用散文表达。

## Summary

```
## Summary
[summary]: #summary

One paragraph explanation of the feature.
```

**观察**:一段话。极简。

## Motivation

```
## Motivation
[motivation]: #motivation

Any changes to Rust should focus on solving a problem that users of Rust are having.
This section should explain this problem in detail, including necessary background.

It should also contain several specific use cases where this feature can help a user,
and explain how it helps.

This section is one of the most important sections of any RFC, and can be lengthy.
```

**观察**:明确允许"可以很长"。和 sdd-kit spec 禁止冗长动机论述是**反方向**的。

## Guide-level explanation / Reference-level explanation(核心分层)

```
## Guide-level explanation

Explain the proposal as if it was already included in the language and you were
teaching it to another Rust programmer. That generally means:

- Introducing new named concepts.
- Explaining the feature largely in terms of examples.
- Explaining how Rust programmers should *think* about the feature
- If applicable, provide sample error messages, deprecation warnings, or migration guidance.

## Reference-level explanation

This is the technical portion of the RFC. Explain the design in sufficient detail that:

- Its interaction with other features is clear.
- It is reasonably clear how the feature would be implemented.
- Corner cases are dissected by example.
```

**关键观察**:**同一特性两层描述** —— Guide-level(用户视角,举例驱动) vs Reference-level(技术细节,实现层)。这是 Rust RFC 的标志性结构。它把"同一主题的两种抽象层次"做成两个独立章节。

## Rationale and alternatives(合并章节)

```
## Rationale and alternatives

- Why is this design the best in the space of possible designs?
- What other designs have been considered and what is the rationale for not choosing them?
- What is the impact of not doing this?
- If this is a language proposal, could this be done in a library or macro instead?
```

**观察**:Rationale 和 Alternatives **合并为一节**,四个子问题作为结构。KEP 是拆成 Drawbacks 和 Alternatives 两节,Rust 是合并。

## Prior art(强制"看看别人怎么做的")

```
## Prior art

Discuss prior art, both the good and the bad, in relation to this proposal.
A few examples of what this can include are:

- For language, library, cargo, tools, and compiler proposals: Does this feature
  exist in other programming languages and what experience have their community had?
- For community proposals: Is this done by some other community and what were their experiences?

If there is no prior art, that is fine - your ideas are interesting to us whether they
are brand new or if it is an adaptation from other languages.

Note that while precedent set by other languages is some motivation, it does not on
its own motivate an RFC.
```

**观察**:**Prior art 是独立必选章节**。要求明确讨论其它语言/社区做过什么。这是 Rust RFC 的独特设计 —— 用结构防止闭门造车。

## Unresolved questions(关键章节)

```
## Unresolved questions

- What parts of the design do you expect to resolve through the RFC process
  before this gets merged?
- What parts of the design do you expect to resolve through the implementation
  of this feature before stabilization?
- What related issues do you consider out of scope for this RFC that could be
  addressed in the future independently of the solution that comes out of this RFC?
```

**关键观察**:**承认 RFC 定稿时仍可能有未决项**,但必须显式列出。这和 sdd-kit 的"Finalize 前必须清空所有 TODO-DECIDE"是**不同策略**:

- sdd-kit: 未决项 = 阻止定稿(必须先决定再 accept)
- Rust RFC: 未决项 = 显式列出(承认某些问题要留到实现阶段或后续 RFC)

Rust 策略的理由: 语言设计演化中,某些问题只有真正实现后才能知道怎么决策。

## Future possibilities

```
## Future possibilities

Think about what the natural extension and evolution of your proposal would be...

This is also a good place to "dump ideas", if they are out of scope for the
RFC you are writing but otherwise related.

If you have tried and cannot think of any future possibilities, you may simply
state that you cannot think of anything.

Note that having something written down in the future-possibilities section is not
a reason to accept the current or a future RFC.
```

**观察**:"允许明确写'想不到后续可能'" —— 模板预设了"未来扩展"位置,但也明示 "此章节不能成为 RFC 被接受的理由"。结构上允许"dump ideas",同时语义上约束"不承诺实现"。

## 模板整体风格

- **所有章节都是 H2**,无嵌套 H3
- **每节顶部有 `[name]: #anchor` 锚点**,便于交叉引用
- **注释指引用段落式英文**,不用 HTML comment
- **无 checkbox、无 frontmatter、无 mandatory 标签**
- **无示例 snippet**,完全是抽象模板
