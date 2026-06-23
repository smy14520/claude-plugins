---
description: 独立审 PRD：查访谈遗漏 + PRD 假设与现有代码的出入。brainstorm 后、impl 前的手动 gate。
---

独立审 `.arbor/tasks/<task>/` 的 PRD（prd.md + slices/）。brainstorm 自审有确认偏见——独立 reviewer 换视角、读代码，抓 brainstorm 自审容易漏的两类问题：

- **访谈遗漏**：AC 不可证伪、漏的场景/边界/非功能、交付面失衡。
- **代码出入**：PRD 的技术假设（选型/数据模型/API/接缝）与现有代码现状不一致（已有项目尤其值得审查）。

这是 brainstorm 后、impl 前的手动 gate——在写代码前修 PRD，比改代码便宜。

**步骤**：
1. 派**独立 reviewer**（子代理，独立上下文，**不看 brainstorm 的访谈推理**；可用不同模型进一步减偏见）：
   - **审 PRD 结构**：每条 AC 真可证伪（Given/When/Then 与失败路径）？切片依赖顺序是否合理、纵向是否完整不割裂？交付面平衡（是否有交付面只剩 `[judge]`、缺 `[assert]` 出口）？质量基线是否可执行（有 rubric/score-file 支撑）？漏关键场景/边界/非功能？
   - **读现有代码**对 PRD（已有项目）：PRD 的技术假设与代码现状一致吗？假设"已有"的真存在吗？有没有已部分实现或冲突的？
   - **易过期事实带 `查证于` 的默认信任**：版本/API/兼容性这类事实，PRD 标了 `查证于 <日期>(<来源>)` = 已查证，默认信；要否定必须重新查证引源，**不准凭知识库/记忆反驳**（记忆滞后，会像"没有 Laravel 13"那样误报）。
2. 产出**严重程度清单**（CRITICAL/HIGH/MEDIUM/LOW）：每条声明及其证据（PRD 行号 或 代码 file:line）。区分"遗漏"和"出入"。
3. 清单交用户。用户据此改 PRD（按 brainstorm 的「修改既有 PRD」流程，并在变更记录中注明），或让 brainstorm 继续提问补全。改完可重复跑 `/seed-kit:review-prd`，直到无 CRITICAL/HIGH 问题。

独立审查是核心价值——防确认偏见，用代码现实校验 PRD 假设。
