---
name: audit
description: "代码库与架构双轴体检流：宏观审计（architect 放置与债务）与微观体检（review 代码异味）。在摸底系统健康度、立项重构或排查架构腐化时使用。"
disable-model-invocation: true
---

# Audit — 代码库与架构双轴体检流

站在系统长期演进与维护者视角，对当前工作区或特定模块进行系统性体检。

## 执行操典

依次调起两个维度的专业审计：

1. **宏观架构轴**：执行 **Call the Skill tool for "architect"**：
   - **放置裁决**：核心机制与实体的归属是否清晰？是否存在第二入口？
   - **不可逆预警**：是否有现在便宜但未来推翻代价极大的架构债务（One-way doors）？
   - **形态退化**：依赖方向是否腐化？是否存在虚假/投机抽象？
2. **微观代码轴**：执行 **Call the Skill tool for "review"**：
   - **Fowler 坏味道基线**：重复代码、过长方法、依恋情结、基本类型偏执等；
   - **深模块度量**：接口是否足够薄？内部实现是否良好封装？

## 产出与退出准则（Completion Criterion）

- **高风险项（Critical / Irreversible）**：必须立即解决的放置错误或契约缺陷，附带明确的 `file:line` 与修改建议；
- **优化机会（Opportunities）**：可加深模块、清理坏味道的具体候选；
- **Completion criterion**：在对话中呈递完整的双轴体检报告，供人类决策是否立项重构；
- **只提供建议与改法，不直接改动业务代码**。

## 反模式（Anti-Patterns）

- **Nitpicking Over Architecture**：把主要篇幅花在代码换行或标点上，对宏观的循环依赖视而不见。
- **Action Without Human Sign-off**：体检后未经人类拍板，擅自对生产代码发起大范围重构。
