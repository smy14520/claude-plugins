# 四态审查状态机

Review 衡量的是：**actual diff 中当前 T-xxx 对应部分，是否在语义上满足 package-local PRD slice + task**。单个 T-xxx verdict 不等于 package PR approval；package readiness 由所有 required T-xxx 的 review 状态聚合得出。

## APPROVED

**含义**：当前 T-xxx 对应的 diff 实现了相关 PRD slice，遵守 task 范围，满足关键约束。无保留意见。

## APPROVED_WITH_NOTES

**含义**：语义层正确，但审查者标记了非阻断性的轻微问题。

## NEEDS_REWORK

**含义**：diff 与 PRD / task 之间存在语义缺口。Impl 必须重新处理。

## BRAINSTORM_DRIFT

**含义**：diff 看起来合理，但 PRD 本身是错误的、失效的或不可行的。退回 brainstorm 更新 `prd.md`，而非 impl。
