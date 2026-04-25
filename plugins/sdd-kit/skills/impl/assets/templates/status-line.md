# task.json 状态转换参考

每次报告都通过 `tools/arbor.py` 更新 task package 的 `task.json`。不要创建 `status.md`，不要写 markdown TODO/checklist；`task.json` 是唯一生命周期状态源。

## 顶层 lifecycle 字段

```json
{
  "state": "planned | ready | in_progress | needs_context | blocked | impl_done | reviewed | needs_rework | brainstorm_drift | completed | superseded",
  "current_phase": "brainstorm | task | impl | self_check | review | complete",
  "active_task": "T-NNN | null",
  "next_action": {
    "skill": "brainstorm | task | impl | review | user | none",
    "task_id": "T-NNN | null",
    "reason": "<why this is the next move>"
  }
}
```

## Pick 转换

开始执行某个 ready task 时：

```text
python3 plugins/sdd-kit/tools/arbor.py set-phase <name> --phase impl --actor impl --task T-NNN --note "implementation started"
python3 plugins/sdd-kit/tools/arbor.py set-status <name> --task T-NNN --state in_progress --actor impl --note "implementation started"
```

机械结果应等价于：

```json
{
  "state": "in_progress",
  "current_phase": "impl",
  "active_task": "T-NNN",
  "tasks[].state": "in_progress"
}
```

同时追加 `phase_history`。

## DONE / DONE_WITH_CONCERNS

验收通过后，对应 `tasks[]` 内的 T-NNN：

```json
{
  "id": "T-NNN",
  "state": "done | done_with_concerns",
  "ready": true,
  "last_impl_result": {
    "state": "DONE | DONE_WITH_CONCERNS",
    "at": "YYYY-MM-DDTHH:MM:SS",
    "summary": "acceptance N/N passed",
    "acceptance": [
      { "check": "<command or predicate>", "result": "passed", "evidence": "<short output or observation>" }
    ],
    "concerns": []
  },
  "updated_at": "YYYY-MM-DDTHH:MM:SS"
}
```

Use script state updates for the lifecycle state:

```text
python3 plugins/sdd-kit/tools/arbor.py set-status <name> --task T-NNN --state done --actor impl --note "acceptance N/N passed"
python3 plugins/sdd-kit/tools/arbor.py set-status <name> --state impl_done --actor impl --note "implementation reported DONE; semantic audit pending"
python3 plugins/sdd-kit/tools/arbor.py set-phase <name> --phase review --actor impl --task T-NNN --note "semantic audit pending"
```

Then set `next_action.skill = review` if needed. If the helper lacks a narrow command for `next_action`, update the helper before hand-editing JSON.

## NEEDS_CONTEXT / BLOCKED

无法继续时：

```text
python3 plugins/sdd-kit/tools/arbor.py set-status <name> --task T-NNN --state needs_context --actor impl --note "<specific missing context>"
```

or:

```text
python3 plugins/sdd-kit/tools/arbor.py set-status <name> --task T-NNN --state blocked --actor impl --note "<specific environment blocker>"
```

顶层 `next_action.skill` 应指向真正解除阻塞的阶段：`task`、`brainstorm` 或 `user`。

## phase_history 追加项

每次状态转换追加一项，不折叠历史：

```json
{
  "at": "YYYY-MM-DDTHH:MM:SS",
  "phase": "impl",
  "task_id": "T-NNN",
  "from": "in_progress",
  "to": "done",
  "actor": "impl",
  "note": "acceptance N/N passed"
}
```

## 规则

1. **task.md 不可修改**。
2. **task.json 是状态事实源**。
3. **不要写 `完成项` / `未完成项` / 普通 TODO**。
4. **DONE 前必须记录 acceptance 结果**。
5. **NEEDS_CONTEXT / BLOCKED 必须记录具体解除条件**。
6. **review 结果写入 `last_review_result`，不要覆盖 `last_impl_result`**。
7. **优先扩展 helper，再手改 JSON**。
