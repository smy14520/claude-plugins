# 四态审查状态机

Review 衡量的是：**diff 是否在语义上满足 brainstorm + task**。

## APPROVED

**含义**：diff 实现了 brainstorm 的目标，遵守 task 范围，满足关键约束。无保留意见。

## APPROVED_WITH_NOTES

**含义**：语义层正确，但审查者标记了非阻断性的轻微问题。

## NEEDS_REWORK

**含义**：diff 与 brainstorm / task 之间存在语义缺口。Impl 必须重新处理。

## BRAINSTORM_DRIFT

**含义**：diff 看起来合理，但 brainstorm 本身是错误的、失效的或不可行的。退回 brainstorm，而非 impl。
