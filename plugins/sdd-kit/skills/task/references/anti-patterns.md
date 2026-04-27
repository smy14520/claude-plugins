# Task 反模式

观察到的失败模式。全部需要避免。

---

## 1. 任务中包含 wikilink

**为什么错误**：任务文件必须自足。执行者只读一个文件。

**修正**：将必要信息内联到 `context:` 或 `notes:`。来源引用使用 `SRC-*`，不是 `[[wikilink]]`。

---

## 2. 需要阅读 PRD 的任务

**症状**：任务写着"按 PRD X 节实现"，但没有具体说明。

**为什么错误**：执行者需要交叉阅读；PRD 会漂移；任何歧义在 impl 时都会变成决策时间。

**修正**：将相关信息直接复制到任务的 `context:` / `acceptance:` 中。Brainstorm 是权威来源；任务是执行单元。

---

## 3. "调研 X" 任务

**为什么错误**：调研属于 research。到 task 阶段时，我们应该已知道方向。

**修正**：退回 research 或 PRD。

---

## 4. "决定 Y" 任务

**为什么错误**：高层决策属于 PRD 阶段。Impl 不应替你拍板。

**修正**：回到 PRD，解决后再重新拆分。

---

## 5. 对琐碎工作的过度拆分

**修正**：使用 lean 模式，或合并成一个任务。一个好的测试：如果人类会把它做成一个原子提交，那它就是一个任务。

---

## 6. 大杂烩任务

**症状**：一个任务覆盖多个里程碑目标，deliverable 一串文件。

**修正**：按 milestone / slice 先切，再拆成 child task。

---

## 7. 缺少 depends-on

**为什么错误**：执行者按错误顺序运行任务，遇到缺失依赖。

**修正**：根据 deliverable / context / shared task 正确填充 `depends-on`。

---

## 8. 不可验证的验收标准

**修正**：每条 acceptance 必须是命令、文件状态检查、HTTP 调用结果或明确二元判断。

---

## 9. 重新编号 ID

**修正**：ID 只追加。永不重用。

---

## 10. 自动推进到 impl

**修正**：task skill 结束于任务文件写入与摘要，不自动实现。

---

## 11. 缺少 task-local context

**症状**：deliverable 很清楚，但执行者不知道本任务在大 feature 中的职责边界。

**修正**：为每个任务写简短 `context:`，说明本任务负责什么、不负责什么。

---

## 12. 缺少 sources

**症状**：任务结论无来源，impl 无法回溯为什么要这样做。

**修正**：列出与该任务直接相关的 `SRC-*`，不多不少。

---

## 13. ready-check 形同虚设

**症状**：把所有 open question 都写进 every task 的 blockers，导致整个任务文件无人可做。

**修正**：只记录真正阻塞该任务的未决项。不要用全局未决项瘫痪所有任务。

---

## 14. 把 T-xxx 当成独立 PR / worktree / branch

**症状**：为 `T-001`、`T-002` 各自创建 branch/worktree/PR，导致一个 package 的语义边界被拆散。

**为什么错误**：sdd-kit 中 package 是执行边界；T-xxx 是 package-local control / acceptance / review 单元。

**修正**：如果某个 T-xxx 真的需要独立 PR，把它提升为新的 `.arbor/tasks/<package>/`，并在 map 中记录 package 依赖。

---

## 15. 一个 package 塞入多个应独立交付的目标

**症状**：一个 `prd.md` 里包含多个可以独立 branch/worktree/PR 的目标。

**为什么错误**：package 是执行边界。把多个可独立交付目标塞进一个 package，会让多 agent、worktree、review 和 PR 都变粗，只剩 T-xxx 在内部硬控。

**修正**：拆成多个 package，用 map 维护它们之间的 dependency / contract；不要只靠 T-xxx 硬塞。

---

## 16. 跳过 upstream package sizing 直接生成长 T-xxx 列表

**症状**：PRD 覆盖多个业务域，task 阶段直接产出 15-20 个 T-xxx，并宣称可以多 agent 执行。

**为什么错误**：T-xxx 是 package-local 控制单元，不是并行执行边界。长列表会掩盖真正应该拆 package 的事实。

**修正**：brainstorm/map 先输出 package graph，并用 `create-split-packages` materialize child package stubs（记录 `split_applied`）；用户确认后，对每个 child package 走 package-local brainstorm/PRD，再分别拆 T-xxx。

---

## 17. 为 large initiative 创建 `.arbor/tasks/<initiative>/`

**症状**：brainstorm 一开始就为上位主题创建 task package，之后 task 又发现它应该拆成多个 package。

**为什么错误**：`.arbor/tasks/<package>/` 本身宣称自己是 branch/worktree/PR 执行边界；用它承载 initiative 会让后续拆包和执行边界对冲。

**修正**：先 route。large initiative 创建 `.arbor/maps/<initiative>/map.md` + `map.json`，并立即把 map 中确认的 executable packages materialize 为 `.arbor/tasks/<package>/` stubs；不要创建 parent initiative task package。后续用 `map-check` / `map-plan-agents` 统筹 execution_ready / prep_ready / blocked 与 worker context。

---

## 18. Task 忽略 missing/stale boundary sizing

**症状**：`package_sizing.status=unchecked` 或明显 stale，task 仍继续拆 T-xxx。

**为什么错误**：task 只是 secondary guard。它不能靠一个长任务列表修复错误的 package boundary。

**修正**：停止，回到 brainstorm/map 更新 boundary decision；只有 `fits_package` 或 `split_applied` 才进入 T-xxx decomposition。
