# Review 工作流：收集 / 判定 / 报告

Review 对 impl 产出执行**语义审计**，依据是 brainstorm + task + diff +（可选）wiki。它绝不修改代码、brainstorm 或任务。

## 收集

1. 解析目标（task ID / 文件 / 最近 DONE）
2. 解析 brainstorm：
   - 优先从任务头部的 `source` / `source_type` 找到 `.claude/brainstorms/<name>.md`
   - 若是 legacy-spec，则读取 `.claude/specs/<name>.md`
   - 若无上游文档，则退回轻量审查
3. 读取任务条目 + 状态日志
4. 检查实际 diff
5. 可选做 wiki 交叉检查

## 判定

将 diff 与 brainstorm + task 仔细比对：
- 目标 / Desired outcomes 是否被覆盖
- In scope / Out of scope 是否被尊重
- task 的 deliverable / acceptance / context / ready-check 是否被满足
- 关键约束 / 来源支持的假设是否被违背
- wiki gotcha 是否被违反
- diff 是否有范围蔓延或关键路径缺口

状态：
- APPROVED
- APPROVED_WITH_NOTES
- NEEDS_REWORK
- BRAINSTORM_DRIFT

## 报告

- 追加到 `## Review log`
- 结构化摘要中说明：
  - 审查对象
  - 依据的 brainstorm / task / diff
  - 关键证据
  - 建议下一步

下一步指引：
- APPROVED → 可继续合并 / 发布
- APPROVED_WITH_NOTES → 可继续，但建议 follow-up
- NEEDS_REWORK → 回 `/sdd-kit:impl`
- BRAINSTORM_DRIFT → 回 `/sdd-kit:brainstorm`
