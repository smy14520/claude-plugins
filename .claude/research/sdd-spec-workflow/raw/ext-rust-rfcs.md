# Rust RFC Process

- URL: https://rust-lang.github.io/rfcs/introduction.html
- 类型: 传统开源工程的 substantial change 文档门禁流程
- 收集日期: 2026-04-22

## 原始要点

- Rust RFC 流程的目标是：为重大变更提供一致、可控的路径。
- 明确区分：
  - 普通改动可直接走 PR
  - “substantial” 变更必须先走 RFC
- 官方说明：若未先走 RFC 就提交新特性实现 PR，PR 可能被关闭，并要求先提交 RFC。
- RFC 基本生命周期：
  - 预讨论 / pre-RFC
  - 提交 RFC markdown
  - 讨论与修订
  - FCP（final comment period）
  - merged / closed / postponed
  - accepted 后进入 implementation issue / PR
- DeepWiki 总结的 RFC 模板内容包含：summary、motivation、guide-level explanation、reference-level explanation、drawbacks、alternatives、prior art、unresolved questions、future possibilities 等。

## 对 workflow 结构的直接观察

- Rust RFC 并不是 spec-first coding toolkit，但它提供了一个非常重要的结构性思想：并非所有改动都要写 spec，只有“重大改动”才触发重流程。
- 它把“是否需要进入文档流程”本身做成门禁条件，这对 workflow 设计非常关键。
- 文档的作用首先是社区共识与设计审议，而不是直接驱动 AI 执行。
- 因为 accepted RFC 仍可后续调整，它也说明：文档门禁不是无限刚性，而是“先形成足够强的可讨论对象”。

## 证据摘录

> Some changes though are “substantial”, and we ask that these be put through a bit of a design process.

> If you submit a pull request to implement a new feature without going through the RFC process, it may be closed with a polite request to submit an RFC first.

> Once an RFC becomes “active” then authors may implement it.

## 适合后续比较的维度

- 哪类变更必须先有 spec / proposal
- 哪类变更可以直接 impl
- spec 的主要角色是“共识门禁”还是“执行控制面”
- 接受后的文档是否允许轻微修订 / 后续 RFC 覆盖
