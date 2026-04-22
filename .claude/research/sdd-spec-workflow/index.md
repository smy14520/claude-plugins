---
status: open
topic: sdd-spec-workflow
updated: 2026-04-22
---

# SDD / Spec Workflow Research

## 当前理解
用户希望为“一套工作流”收集与 SDD（spec-driven development / spec-first development）相关的优秀开源项目、工程实践与方法论，用来提炼后续可进入 spec 的工作流设计输入。重点不是单个模板，而是：哪些项目真的把需求/规范作为中间工件来驱动实现、任务拆解、审查或自动化执行。

## 当前研究范围
- 开源项目中与 spec-first / design-doc-first / RFC-first / ADR-aware workflow 相关的代表性样本
- 这些样本中的工件类型、阶段边界、推进条件、协作方式
- 对本项目 research → spec → task → impl 工作流的启发
- AI 辅助开发里“spec 作为控制面”的新做法

## 暂不纳入
- 纯模板仓库但没有真实工作流约束的项目
- 仅讨论“怎么写产品需求文档”但与工程执行脱节的材料
- 与 spec 无关的普通项目脚手架

## 已知
- 当前项目正在向 research → spec → task → impl 的窄职责阶段迁移
- 用户这次需要的是“优秀开源项目或思想”样本集合，而不是立即冻结方案

## 待验证假设
- “优秀样本”应优先关注有明确 stage boundary、工件约束、handoff 机制的项目，而不只是漂亮模板
- 除了直接叫 SDD 的项目，还应纳入 RFC/ADR/design-doc 驱动的成熟工程方法作为平行参照
- AI coding 工作流里的 spec-first 实践会对当前项目尤其相关

## 待澄清问题
- 当前项目是否需要 project-level context artifact（类似 constitution / product / tech-stack）？
- 当前项目中的 spec 应更接近 feature contract，还是 change proposal + design bundle？
- 哪些改动必须先进入 research/spec/task 流程，哪些可以直接 impl？
- workflow 级长期决策是放进规则文件，还是单独 decision/ADR 层？

## 主题导航
- [AI spec-first 工具链](notes/ai-spec-first-toolkits.md)
- [RFC / KEP / 文档门禁流程](notes/rfc-kep-and-doc-gates.md)
- [ADR 与决策记录层](notes/adr-and-decision-layer.md)
- [对当前项目最有价值的 workflow 设计原则](notes/workflow-design-principles.md)

## 关键来源
- `raw/ext-github-spec-kit.md`
- `raw/ext-openspec.md`
- `raw/ext-spec-kitty.md`
- `raw/ext-conductor-flow.md`
- `raw/ext-mindfold-trellis/_manifest.md`
- `raw/ext-andrej-karpathy-skills.md`
- `raw/ext-rust-rfcs.md`
- `raw/ext-kubernetes-kep.md`
- `raw/ext-adr-and-async-pr.md`

## 当前是否适合进入 spec
还**不建议直接冻结完整 workflow spec**，但已经足够进入“下一轮收敛”：
- 可以开始挑选要借鉴的结构原则
- 可以讨论哪些阶段/工件是真正要保留的
- 可以进一步限定进入完整流程的触发条件

换言之：现在更适合做 **workflow framing / principles spec**，还不适合直接写最终定版的全流程规范。

## 下一步
- check：判断是否要进入“workflow principles spec”
- 若继续 research：补一轮“哪些任务不该进入 spec 流程”的反例样本
- 若开始收敛：把本轮原则压缩成一份更短的候选 workflow 方案比较
