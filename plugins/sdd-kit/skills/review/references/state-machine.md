# 四态审查状态机

Review 衡量的是：**actual diff 是否在语义上满足 package PRD scope、Acceptance Criteria 与 Technical Framing**。Review verdict 不等于 PR approval、merge 或 release。

## APPROVED

**含义**：当前 diff 实现了 PRD scope，满足关键约束和验收。无保留意见。

## APPROVED_WITH_NOTES

**含义**：语义层正确，但审查者标记了非阻断性的轻微问题。

## NEEDS_REWORK

**含义**：diff 与 PRD / impl evidence 之间存在语义缺口。Impl 必须重新处理。

## BRAINSTORM_DRIFT

**含义**：diff 看起来合理，但 PRD 本身是错误的、失效的或不可行的。退回 brainstorm 更新 `prd.md`，而非 impl。
