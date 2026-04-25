# Review 反模式

观察到的失败模式。全部需要避免。

---

## 1. 橡皮图章式 APPROVED

APPROVED 不能只是 "LGTM"。至少要说明 goal / scope / constraints / diff scope。

---

## 2. 只读任务文件，不看 git diff

没有 diff 检查就没有审查。

---

## 3. 将"验收通过"等同于"上游意图已满足"

验收成功只是必要条件，不是充分条件。Review 仍须检查 PRD + task 语义。

---

## 4. 在审查中直接修改代码

Review 是只读的。修复属于 impl 的下一轮。

---

## 5. 用 APPROVED_WITH_NOTES 掩盖真正的 NEEDS_REWORK

如果关键约束 / 关键路径缺失，就不是 notes，而是 rework。

---

## 6. 将 impl 猜测错误归为 BRAINSTORM_DRIFT

如果上游足够清晰而 impl 猜错了，那是 NEEDS_REWORK，不是 drift。

---

## 7. 用 BRAINSTORM_DRIFT 表示“PRD 可以更清晰”

只有在 PRD 真正错误、失效、不可行时才用 drift。

---

## 8. 静默跳过 wiki 交叉检查

应显式说明检查了哪些 wiki gotcha，或为什么本次跳过。
