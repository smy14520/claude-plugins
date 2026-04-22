# Kubernetes KEP Process

- URL: https://github.com/kubernetes/enhancements/blob/master/keps/sig-architecture/0000-kep-process/README.md
- 类型: 大型开源项目的 enhancement proposal 流程
- 收集日期: 2026-04-22

## 原始要点

- KEP 的目标是为 Kubernetes 变更提供统一结构、清晰动机、稳定性里程碑与可持续跟踪。
- KEP 被定义为结合以下三类角色于一体的工件：
  - feature / effort-tracking document
  - product requirements document
  - design document
- 明确指出：任何 user/operator-facing enhancement，或影响大范围开发社区的技术改动，都应考虑使用 KEP。
- KEP 的重要结构元素：
  - `README.md`：summary / motivation / proposal / design details / graduation criteria / PRR / implementation history / drawbacks / alternatives
  - `kep.yaml`：title / status / authors / owning-sig / reviewers / approvers / editor / dates / supersession 等 metadata
- KEP workflow 有显式状态：`provisional`、`implementable`、`implemented`、`deferred`、`rejected`、`withdrawn`、`replaced`。
- 它强调 approvers、editor、cross-SIG coordination、metrics，说明其目标不只是写文档，而是治理复杂协作。

## 对 workflow 结构的直接观察

- KEP 相比 Rust RFC 更进一步，把 product / design / delivery tracking 融合在一个长期工件里。
- 它适用于跨团队、跨版本、生命周期长的增强项。
- `kep.yaml` 这种 metadata 设计很值得注意：状态、责任人、替代关系都结构化了，便于工具化。
- 对小团队或单人项目来说它可能偏重，但对“复杂特性如何被治理”很有启发。

## 证据摘录

> A KEP attempts to combine aspects of a feature and effort-tracking document, a product requirements document, a design document into one file.

> The KEP process is the way that SIGs can negotiate and communicate changes that cross boundaries.

> status must be one of provisional / implementable / implemented / deferred / rejected / withdrawn / replaced.

## 适合后续比较的维度

- 单工件承载多角色，还是拆成 proposal/spec/design/tasks 多工件
- 是否需要结构化 metadata 来支持工具化与状态治理
- 是否需要 ownership / reviewer / approver 等角色字段
- 是否需要 lifecycle / graduation / superseded 之类长期状态
