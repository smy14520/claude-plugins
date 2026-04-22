# Impl 工作流：Pick / Execute / SelfCheck / Report

四个原语的详细流程。SKILL.md 给出高层步骤；本文件给出完整工作流，包括边界情况和 ad-hoc 模式。

> **范围提醒**：Impl 的 `SelfCheck` 只运行任务自身的 `acceptance:` 命令。它不对 brainstorm 做语义审计——那是 `review` skill 的职责。

---

## Pick

### 触发短语

- "实施 T-003"
- "执行下一个 task"
- "run next task for brainstorm X"
- "start impl on <task-file>"

### 完整流程

1. 定位 task 文件
2. 读取任务列表 + 状态日志
3. 查找可执行任务：Pending + `depends-on` 满足 + `ready-check` 无阻塞
4. 如果用户指定具体 ID，但该任务仍被 blockers 阻塞，明确指出 blockers
5. 选择后向用户确认再执行

## Execute

### 完整流程

1. 读取 `deliverable + acceptance + context + sources + notes`
2. 规划最小差异：能让所有 acceptance 通过的最小变更
3. 按需读取 brainstorm 作为背景，但不重新做高层选择
4. 处理歧义：
   - task 说 X，brainstorm 背景暗示 Y，但 task 未冻结 → `NEEDS_CONTEXT`
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

- 向 `## Status log` 追加状态行
- NEEDS_CONTEXT 行可引用：`brainstorm §X / task <field> / SRC-...`
- 绝不改写既有状态行
