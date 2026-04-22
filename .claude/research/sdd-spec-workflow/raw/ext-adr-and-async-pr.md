# ADR and Async PR-based Decision Making

- URL 1: https://github.com/joelparkerhenderson/architecture-decision-record
- URL 2: https://github.com/openscd/.github/blob/main/doc/adr/0002-use-pull-requests-and-adrs-for-async-decision-making.md
- 类型: 决策记录与异步协作流程
- 收集日期: 2026-04-22

## 原始要点

### ADR 基础方法

- ADR 用于记录重要架构决策及其 context 与 consequences。
- joelparkerhenderson 仓库强调：ADR 的价值在于保留“为什么这样做”的信息，而不是事后填表。
- 常见模板核心包含：Context / Decision / Consequences；扩展模板还会加入 options、pros/cons、business case 等。
- 该仓库还强调 immutability / supersede、文件命名规范、decision lifecycle、decision guardrails for pull requests、fitness functions for decisions as code。

### OpenSCD 的 async 决策实践

- 通过 ADR PR 的方式进行异步设计决策。
- ADR 没有专门 draft 状态：未 merge 的 PR 即 draft，被拒 PR 即 rejected。
- ADR 需要包含：Date / Status / Context / Decision / Consequences。
- PR 标题统一前缀 `ADR:`，PR 描述可包含 target review date 与特定问题。
- 其目标是解决跨公司、跨时区社区的理解断层，并提供可扩展的异步沟通模式。

## 对 workflow 结构的直接观察

- ADR 不是完整 feature workflow，但非常适合补足“为什么这样设计”的决策层。
- OpenSCD 的实践很值得借鉴：把 PR 本身作为 draft / review 容器，从而避免额外的状态系统。
- ADR 更适合记录横切性原则、关键技术选择、长期约束，而不是逐 feature 的完整执行计划。
- 如果 research/spec workflow 后续缺少决策沉淀层，ADR 会是很好的补件。

## 证据摘录

> An architecture decision record (ADR) is a document that captures an important architecture decision made along with its context and consequences.

> decision records are a way for teams to think smarter and communicate better.

> We will use ADR pull requests similar to an RFC process to collaborate on an architecture decision or design.

## 适合后续比较的维度

- 是否需要单独的“决策记录层”而不把所有内容塞进 spec
- draft / review / accepted 是否可直接借用 PR 生命周期
- 哪些问题属于 feature spec，哪些更适合 ADR
- 是否需要把 decisions 与 CI/PR guardrails 连接起来
