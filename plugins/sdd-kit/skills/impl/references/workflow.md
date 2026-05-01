# Impl 工作流：Pick / Execute / SelfCheck / Report

四个原语的详细流程。SKILL.md 给出高层步骤；本文件给出完整工作流，包括边界情况和 ad-hoc 模式。

> **范围提醒**：Impl 的 `SelfCheck` 只运行任务自身的 `acceptance:` 命令。它不对 PRD 做语义审计——那是 `review` skill 的职责。

---

## Pick

### 触发短语

- "实施 <package> 的 T-003"
- "执行 <package> 下一个 task"
- "run next task for package X"
- "start impl on <task-file>"

### 完整流程

1. 先确认 package，再确认 package-local T-xxx；裸 `T-001` 不是全局唯一任务
2. 定位 task package：`.arbor/tasks/<name>/task.md`，并读取 `.arbor/tasks/<name>/task.json`、`prd.md`、`context/impl.jsonl`、`context/sources.jsonl`
3. 读取任务列表 + 结构化状态元数据，包括 `execution` package boundary
4. 查找可执行任务：`ready` + `depends_on` 满足 + `ready-check` 无阻塞
5. 如果用户指定具体 ID，但该任务仍被 blockers 阻塞，明确指出 blockers
6. 选择后向用户确认再执行
7. 开始执行时用 `sdd-arbor set-status <name> --task T-xxx --state in_progress --actor impl --note "implementation started"` 记录 active task

## Execute

### 完整流程

1. 读取 `deliverable + acceptance + context + sources + notes`
2. 规划最小差异：能让当前 T-xxx acceptance 通过的最小变更，并限制在 package boundary 内
3. 按需读取 package-local `prd.md` 作为背景，但不重新做高层选择
4. 处理歧义：
   - task 说 X，PRD 背景暗示 Y，但 task 未冻结 → `NEEDS_CONTEXT`
   - acceptance 提到了不存在的命令/文件 → `NEEDS_CONTEXT`
   - ready-check 明确指出 blocker 未解除 → `BLOCKED`

## SelfCheck

1. 解析 acceptance 块
2. 按顺序运行命令 / 文件谓词 / HTTP 谓词
3. 收集结果
4. 全部通过 + 无妥协 → DONE
5. 全部通过 + 有已记录顾虑 → DONE_WITH_CONCERNS
6. 失败按性质归到 BLOCKED 或 NEEDS_CONTEXT

## Report

- 用 `sdd-arbor record-impl-result` 记录 DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED，以及 summary、acceptance、commands、concerns；helper 更新 `task.json` 聚合状态和 `phase_history`
- 如需补充实现阶段上下文，用 `sdd-arbor add-context <name> --type impl ...` 追加到 `context/impl.jsonl`
- NEEDS_CONTEXT 行可引用：`prd.md §X / task <field> / SRC-...`
- 绝不修改 `task.md`；不要创建 markdown TODO/status checklist
