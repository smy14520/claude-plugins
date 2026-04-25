<!--
Review entry format. Append to task package `review.md` for human-readable audit history.

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
- [✓] T-003 (APPROVED) — 2026-04-24 16:40 — PRD goal met; task scope respected; diff clean
```

### APPROVED_WITH_NOTES（有轻微问题）

```
- [~] T-004 (APPROVED_WITH_NOTES) — 2026-04-24 16:55 — core correct; timeout hard-coded 5s though task notes imply configurable; src/webhooks/xhs-handler.ts:34
```

### NEEDS_REWORK（存在具体缺陷）

```
- [✗] T-005 (NEEDS_REWORK) — 2026-04-24 17:10 — task acceptance requires burst scenario; diff lacks rate-limit handling; scanned src/webhooks/ and src/mw/
```

### BRAINSTORM_DRIFT（上游收敛文档有误）

```
- [!] T-006 (BRAINSTORM_DRIFT) — 2026-04-24 17:30 — PRD mandates redis for idempotency; no redis dep in package.json; current codebase uses in-memory Map
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

顶层 lifecycle：

```json
{
  "state": "reviewed | needs_rework | brainstorm_drift | completed",
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
