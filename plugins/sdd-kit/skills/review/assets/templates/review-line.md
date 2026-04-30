<!--
Review entry format. Append to task package `review.md` for human-readable audit history.
Each entry is for a package-local T-xxx control unit, not whole-package PR approval.

`review.md` is NOT the latest review state source. After appending an entry, also update
`task.json.tasks[].last_review_result`, task state, top-level lifecycle fields, and
`phase_history`.

Checkbox semantics:
  [✓] — APPROVED
  [~] — APPROVED_WITH_NOTES
  [✗] — NEEDS_REWORK
  [!] — BRAINSTORM_DRIFT
-->

## review.md 示例

### APPROVED（通过）

```
- [✓] T-003 (APPROVED) — 2026-04-24 16:40 — PRD 目标已覆盖；task 范围被遵守；diff 未发现阻塞问题
```

### APPROVED_WITH_NOTES（有轻微问题）

```
- [~] T-004 (APPROVED_WITH_NOTES) — 2026-04-24 16:55 — 核心语义正确；但 timeout 固定为 5s，而 task 备注暗示应可配置；src/webhooks/xhs-handler.ts:34
```

### NEEDS_REWORK（存在具体缺陷）

```
- [✗] T-005 (NEEDS_REWORK) — 2026-04-24 17:10 — task acceptance 要求 burst 场景；diff 缺少 rate-limit 处理；已检查 src/webhooks/ 与 src/mw/
```

### BRAINSTORM_DRIFT（上游收敛文档有误）

```
- [!] T-006 (BRAINSTORM_DRIFT) — 2026-04-24 17:30 — PRD 要求使用 redis 做幂等；package.json 没有 redis 依赖；当前代码库使用 in-memory Map
```

## task.json 更新示例

对应 `tasks[]` 内的 T-NNN：

```json
{
  "id": "T-NNN",
  "state": "approved | approved_with_notes | needs_rework | brainstorm_drift",
  "last_review_result": {
    "state": "APPROVED | APPROVED_WITH_NOTES | NEEDS_REWORK | BRAINSTORM_DRIFT",
    "at": "YYYY-MM-DDTHH:MM:SS",
    "summary": "<short review summary>",
    "evidence": [
      "git diff checked",
      "PRD goal compared",
      "task acceptance evidence checked"
    ],
    "notes": []
  },
  "updated_at": "YYYY-MM-DDTHH:MM:SS"
}
```

顶层 lifecycle 是 package aggregate，不是单个 T-xxx verdict 的简单镜像。只有所有 required T-xxx 都是 `approved | approved_with_notes | skipped` 时，package 才进入 `reviewed` + `next_action.skill=none`。

```json
{
  "state": "ready | reviewed | needs_rework | brainstorm_drift",
  "current_phase": "review",
  "active_task": null,
  "next_action": {
    "skill": "impl | brainstorm | none",
    "task_id": "T-NNN | null",
    "reason": "<why this is next>"
  }
}
```

追加 `phase_history`：

```json
{
  "at": "YYYY-MM-DDTHH:MM:SS",
  "phase": "review",
  "task_id": "T-NNN",
  "from": "done",
  "to": "approved",
  "actor": "review",
  "note": "semantic audit passed"
}
```
