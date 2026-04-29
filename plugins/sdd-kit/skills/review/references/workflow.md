# Review 工作流：收集 / 判定 / 报告

Review 对 impl 产出执行**语义审计**，依据是 package-local PRD + package-local T-xxx task + actual diff +（可选）wiki。它绝不修改代码、`prd.md` 或任务定义。单个 T-xxx verdict 不等于 package PR approval。

## 收集

1. 解析目标（package + package-local T-xxx / 最近 DONE）；裸 `T-001` 不是全局唯一任务
2. 读取 package-local PRD：`.arbor/tasks/<name>/prd.md`
   - 若缺失，可读取 legacy `.arbor/brainstorms/<name>.md` 作为 fallback
   - fallback 必须在报告中标为迁移风险；新流程应回 brainstorm 迁入 `prd.md`
3. 读取 task package 的 `task.md` + `task.json` + 可选 `context/review.jsonl`
4. 检查实际 git diff，并明确当前 T-xxx 的 diff scope
5. 可选做 wiki 交叉检查

## 判定

将 diff 与 PRD + task 仔细比对：
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

- 追加到 `.arbor/tasks/<name>/review.md`
- 使用 `sdd-arbor set-status` / `set-phase` 同步更新 `.arbor/tasks/<name>/task.json` 中对应 T-xxx 的 `state`、`updated_at`、顶层 `state/current_phase/next_action`，并追加 `phase_history`
- `review.md` 是人类可读审计日志；当前 review 状态以 `task.json` 为准
- 结构化摘要中说明：
  - 审查对象
  - 依据的 PRD / task / diff
  - 关键证据
  - 建议下一步

下一步指引：
- APPROVED → 当前 T-xxx 通过；若所有 required T-xxx 都通过 review，package 可进入 PR/final review
- APPROVED_WITH_NOTES → 当前 T-xxx 可计入 package readiness，但建议 follow-up
- NEEDS_REWORK → 回 `/sdd-kit:impl` 处理当前 T-xxx
- BRAINSTORM_DRIFT → 回 `/sdd-kit:brainstorm` 追加 package-local `AMD-xxx`；再由 task 追加新 T-xxx。若边界变化，回 map/user。
