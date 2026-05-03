<!--
Review entry format. Append to package `review.md` for human-readable audit history.
Each entry is for package-level PRD scope, not PR approval.

`review.md` is NOT the latest review state source. After appending an entry, also update
`task.json.review_result`, top-level lifecycle fields, and `phase_history` through sdd-arbor.

Checkbox semantics:
  [✓] — APPROVED
  [~] — APPROVED_WITH_NOTES
  [✗] — NEEDS_REWORK
  [!] — BRAINSTORM_DRIFT
-->

## review.md 示例

### APPROVED（通过）

```
- [✓] APPROVED — 2026-04-24 16:40 — PRD 目标与验收已覆盖；diff 未发现阻塞问题
```

### APPROVED_WITH_NOTES（有轻微问题）

```
- [~] APPROVED_WITH_NOTES — 2026-04-24 16:55 — 核心语义正确；但 timeout 固定为 5s，建议后续配置化；src/webhooks/xhs-handler.ts:34
```

### NEEDS_REWORK（存在具体缺陷）

```
- [✗] NEEDS_REWORK — 2026-04-24 17:10 — PRD acceptance 要求 burst 场景；diff 缺少 rate-limit 处理；已检查 src/webhooks/ 与 src/mw/
```

### BRAINSTORM_DRIFT（上游收敛文档有误）

```
- [!] BRAINSTORM_DRIFT — 2026-04-24 17:30 — PRD 要求使用 redis 做幂等；package.json 没有 redis 依赖；当前代码库使用 in-memory store
```

## task.json 更新示例

```json
{
  "state": "reviewed | doing | draft",
  "current_phase": "review",
  "next_action": {
    "skill": "impl | brainstorm | none",
    "reason": "<why this is next>"
  },
  "review_result": {
    "state": "APPROVED | APPROVED_WITH_NOTES | NEEDS_REWORK | BRAINSTORM_DRIFT",
    "at": "YYYY-MM-DDTHH:MM:SS",
    "summary": "<short review summary>",
    "evidence": [
      "git diff checked",
      "PRD goal compared",
      "acceptance evidence checked"
    ],
    "notes": []
  }
}
```

追加 `phase_history`：

```json
{
  "at": "YYYY-MM-DDTHH:MM:SS",
  "phase": "review",
  "from": "done",
  "to": "approved",
  "actor": "review",
  "note": "semantic audit passed"
}
```
