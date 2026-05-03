# task.json 状态转换参考

每次报告都通过 `sdd-arbor` 更新 package 的 `task.json`。不要创建 `status.md`，不要写 markdown TODO/checklist；`task.json` 是 lifecycle 状态源。PRD `## Slices` 是 impl 进度记录，branch/PR metadata 可记录在 package-level `execution` / `pr`。

## 顶层 lifecycle 字段

```json
{
  "state": "draft | ready | doing | done | reviewed",
  "current_phase": "brainstorm | impl | review | complete",
  "next_action": {
    "skill": "brainstorm | impl | review | user | none",
    "reason": "<why this is the next move>"
  }
}
```

## Pick 转换

开始执行 ready package 时，用 `sdd-arbor set-status <package> --state doing --actor impl --note "implementation started"` 记录。

机械结果应等价于：

```json
{
  "state": "doing",
  "current_phase": "impl",
  "next_action": {
    "skill": "impl",
    "reason": "正在执行"
  }
}
```

同时追加 `phase_history`。

## DONE / DONE_WITH_CONCERNS

验收通过后：

```json
{
  "state": "done",
  "current_phase": "impl",
  "impl_result": {
    "state": "DONE | DONE_WITH_CONCERNS",
    "at": "YYYY-MM-DDTHH:MM:SS",
    "summary": "acceptance N/N passed",
    "acceptance": ["<command or predicate>: passed"],
    "commands": ["<command run>"],
    "concerns": []
  },
  "next_action": {
    "skill": "review",
    "reason": "执行完成，等待审计"
  }
}
```

Use arbor helper `record-impl-result` for structured result evidence.

## NEEDS_CONTEXT / BLOCKED

无法继续时，用 arbor helper `record-impl-result` 记录 `needs_context` 或 `blocked`，并写清具体原因。顶层 package state 保持 `doing`：

- `needs_context` → `next_action.skill=brainstorm`
- `blocked` → `next_action.skill=user`

## phase_history 追加项

每次状态转换追加一项，不折叠历史：

```json
{
  "at": "YYYY-MM-DDTHH:MM:SS",
  "phase": "impl",
  "from": "doing",
  "to": "done",
  "actor": "impl",
  "note": "acceptance N/N passed"
}
```

## 规则

1. **PRD 需求内容不由 impl 静默修改**；impl 只更新 `## Slices` 的 `[ ]` / `[-]` / `[x]` 进度标记。
2. **task.json 是 lifecycle 状态事实源**。
3. **不要写 `完成项` / `未完成项` / 普通 TODO**。
4. **DONE 前必须记录 acceptance 结果**。
5. **NEEDS_CONTEXT / BLOCKED 必须记录具体解除条件**。
6. **review 结果写入 `review_result`，不要覆盖 `impl_result`**。
7. **优先扩展 helper，再手改 JSON**。
