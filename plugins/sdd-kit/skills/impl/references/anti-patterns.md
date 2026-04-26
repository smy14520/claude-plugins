# Impl 反模式

已观察到的失败模式。全部应避免。

---

## 1. 未运行验收即声称 DONE

**修复方式**：SelfCheck 必须执行每一条 `acceptance:`。无法运行则是 BLOCKED，而非 DONE。

---

## 2. 静默做设计决策以解除阻塞

**症状**：任务对 TTL / 重试次数 / URL 有歧义，执行者自行拍板。

**修复方式**：发出 NEEDS_CONTEXT，并引用具体来源（`PRD §X / task <field> / SRC-...`）。

---

## 3. 将 BLOCKED 伪装为 DONE_WITH_CONCERNS

**修复方式**：DWC 只有在 acceptance 通过时才成立。否则就是 BLOCKED 或 NEEDS_CONTEXT。

---

## 4. 修改任务定义使其通过

**修复方式**：impl 不得编辑 task 的 `acceptance:` / `context:` / `ready-check:`。若上游定义有问题，返回 NEEDS_CONTEXT。

---

## 5. 在任务提交中夹带清理工作

**修复方式**：保持任务聚焦于其 deliverable。相邻清理另起任务。

---

## 6. "运行了测试"但不看输出

**修复方式**：检查退出码 + 输出，不做表面通过。

---

## 7. 自动推进到下一个任务

**修复方式**：报告后停止，由用户决定是否继续。

---

## 8. 过度依赖重读 PRD

**症状**：每个 task 都重新把整个 PRD 当主要输入。

**为什么错误**：这会让 task-local 冻结失去意义，重新把高层歧义带回 impl。

**修复方式**：优先信任 task 的 `context + sources + ready-check`。只有在局部背景不足时才回读 PRD。

---

## 9. 重写 PRD 以匹配 impl

**修复方式**：impl 不是 PRD 的权威。若认为上游文档有误，发 NEEDS_CONTEXT 或留给 review 标记 `BRAINSTORM_DRIFT`。

---

## 10. 把 T-xxx DONE 当成 package 完成

**症状**：当前 T-xxx acceptance 通过后，声称整个 package branch/worktree/PR 已完成。

**修复方式**：DONE 只覆盖当前 package-local T-xxx。Package readiness 必须由所有 required T-xxx 的 review 聚合得出。

---

## 11. 在 package branch 中夹带另一个 package 的工作

**症状**：实现当前 T-xxx 时顺手修改另一个 bounded package 的范围。

**修复方式**：停止并返回 NEEDS_CONTEXT / task；若确实需要跨 package 工作，更新 map 或拆出新的 package。
