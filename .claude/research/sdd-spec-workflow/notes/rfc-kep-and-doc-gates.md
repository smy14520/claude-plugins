# RFC / KEP / 文档门禁流程

## 当前结论

Rust RFC 与 Kubernetes KEP 虽然不是“AI coding 的 spec 工具”，但它们提供了设计 workflow 时最关键的结构性思想：**不是所有改动都值得进入重文档流程；必须先定义什么情况下需要 proposal/spec，什么情况下可以直接改。**

### Rust RFC 提供的核心启发

- 为“substantial changes”设置前置门禁
- 重大改动先形成可讨论的 RFC 文档，再进入实现
- 普通修复、文档改动、小改动可直接走 PR
- 文档的第一职责是形成共识与审议对象，而不是直接驱动自动执行

### Kubernetes KEP 提供的核心启发

- 当变更跨团队、跨版本、跨责任域时，单个 PR / issue 不够，需要更稳定的长期工件
- 一个工件可以同时承担 requirements / design / delivery tracking 三种角色
- metadata、状态机、责任人、替代关系都值得结构化，以便工具化与治理

## 来源

- `../raw/ext-rust-rfcs.md`
- `../raw/ext-kubernetes-kep.md`

## 这对需求意味着什么

对当前项目而言，RFC / KEP 类样本的真正价值不是模板本身，而是以下三点：

1. **触发条件必须明确**
   - 哪些任务必须先 research/spec/task
   - 哪些任务可以直接 impl
   - 否则流程会要么失控，要么过重

2. **重流程的目的要说清**
   - 是为了共识？为了减少 agent 漂移？为了跨轮 handoff？为了审计链？
   - 不同目的决定 spec 写法不同

3. **状态与 ownership 可以适度结构化**
   - 即使不做 KEP 那么重，也可借鉴 status / owner / superseded 等元数据

## 仍未解决的问题

- 当前项目是否需要类似 “substantial change only” 的进入 spec 规则？
- 如果需要，判定维度是什么：影响范围、歧义程度、跨文件改动、还是需要设计决策？
- 当前项目的 spec 是否需要 reviewer / approver / status 等 metadata，还是保持轻量即可？

## 相关笔记

- `ai-spec-first-toolkits.md`
- `workflow-design-principles.md`
