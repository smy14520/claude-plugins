# Review 反模式

## 橡皮图章式 APPROVED

APPROVED 不能只是 "LGTM"。至少说明检查了哪些 goal / scope / diff evidence。

## 只读 PRD，不看 git diff

没有 diff 检查就没有审查。

## 将 self-check 通过等同于上游意图已满足

self-check 是 evidence，不是 verdict。Review 仍要检查 PRD、Technical Framing、Slices 和 diff 语义。

## 在审查中直接修改代码

Review 是只读的。修复属于 impl 的下一轮。

## 用 APPROVED_WITH_NOTES 掩盖 NEEDS_REWORK

如果关键约束、关键路径或验收证据缺失，就不是 notes，而是 rework。

## 将 impl 猜测错误归为 BRAINSTORM_DRIFT

如果上游足够清晰而 impl 猜错了，那是 NEEDS_REWORK，不是 drift。

## 用 BRAINSTORM_DRIFT 表示“PRD 可以更清晰”

只有 PRD 真正错误、失效或与当前 repo 脱节时才用 drift。

## 把 package APPROVED 当成 delivered

Review verdict 只说明当前 package scope 满足 PRD。PR merge / release 不是 review 自动完成的事。

## 在 package 累积 diff 中不隔离当前 PRD scope

package diff 可能包含多个来源的变更。报告必须说明当前审计对应哪些 diff files / behavior，并把结论绑定到当前 PRD scope。

## 不检查 impl self-check 的来源

必须检查 impl evidence 如何对应 PRD goal/scope、Acceptance Criteria、Technical Framing 与 Slices。
