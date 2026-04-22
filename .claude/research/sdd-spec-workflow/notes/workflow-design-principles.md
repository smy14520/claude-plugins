# 对当前项目最有价值的 workflow 设计原则

## 当前结论

基于本轮样本，最值得带入当前项目的不是某一个开源框架的全套命令，而是下面这些更稳定的结构原则。

### 1. 先定义进入重流程的触发条件

来源：Rust RFC、Kubernetes KEP

- 不是每个改动都值得走 research → spec → task → impl
- 必须先定义“什么情况必须走完整流程”
- 否则流程会变成负担，或者被随意绕过

建议方向：用“需求歧义大 / 改动范围广 / 需要跨阶段 handoff / 需要显式设计决策”作为触发候选。

### 2. 工件之间要有清晰边界，而不是内容重叠

来源：spec-kit、OpenSpec

- `research` 负责发散与澄清
- `spec` 负责冻结 contract
- `task` 负责拆执行单元
- `impl` 负责按 contract 交付
- 如果每个阶段都重复写一遍需求，workflow 很快会腐烂

### 3. 让工件 repo-native，而不是存在聊天里

来源：spec-kit、OpenSpec、Conductor

- 需求、设计、任务、上下文最好都成为 repo 工件
- 这样才能跨轮继续、跨 agent handoff、做 review、做审计链
- 可移植性来自工件，而不是来自某个特定 agent 的提示词

### 4. 对 brownfield，要区分“当前状态”和“本次变更”

来源：OpenSpec

- 很多 workflow 在 greenfield 看起来很好，但到了存量代码库就容易混乱
- 如果项目主要是增量改动，那么“change-centric”组织往往比“重新写一份全量规范”更现实
- 可以考虑让 spec 更偏向“本次变更的契约”，而不是整个系统说明书

### 5. review 与 archive 不是可有可无的尾巴

来源：OpenSpec、Spec Kitty

- 如果 spec/task/impl 是正式工件，就需要考虑完成后如何验证、如何关闭、如何保留历史
- 否则 workflow 只能启动，不能闭环
- review 不一定重，但应回答“实现是否符合 spec，而不是只是能跑”

### 6. workflow 级决策应与 feature 级 spec 分层

来源：ADR、constitution、product/tech-stack 类工件、karpathy-skills

- 什么时候进 spec、spec 必须有哪些字段、review 怎么判定，这些是 workflow 级问题
- 单 feature spec 不应承载所有长期规则
- 类似 karpathy-skills 的单文件原则很适合承接“默认行为约束”，但不适合承接任务状态与流程结构
- 需要有单独位置存放这类长期决策与原则

## 当前判断

对当前项目最匹配的方向，仍然像是：

- 保留窄职责阶段：research → spec → task → impl
- 借鉴 spec-kit 的阶段分层
- 借鉴 OpenSpec 的 brownfield / change-centric 思路
- 借鉴 RFC/KEP 的“何时必须先写文档”门禁思想
- 谨慎吸收 Spec Kitty 的强执行治理，只在确有需要时引入

## 仍未解决的问题

- 当前项目是否需要 project-level context artifact（类似 constitution / product / tech-stack）？
- spec 是否应该只描述本次 change contract，还是同时容纳 design rationale？
- review 是否应成为正式阶段，还是仅作为可选 skill？

## 相关笔记

- `ai-spec-first-toolkits.md`
- `rfc-kep-and-doc-gates.md`
- `adr-and-decision-layer.md`
