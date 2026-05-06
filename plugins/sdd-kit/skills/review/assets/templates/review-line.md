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
- [~] APPROVED_WITH_NOTES — 2026-04-24 16:55 — 核心语义正确；但 retry timeout 固定为 5s，建议后续配置化；src/integrations/provider-adapter.ts:34
```

### NEEDS_REWORK（存在具体缺陷）

```
- [✗] NEEDS_REWORK — 2026-04-24 17:10 — PRD acceptance 要求 init 命令在已存在目录下安全失败；diff 缺少非空目录检查；已检查 cmd/init 与 tests/init_test.go
```

### BRAINSTORM_DRIFT（上游收敛文档有误）

```
- [!] BRAINSTORM_DRIFT — 2026-04-24 17:30 — PRD 要求保存文件格式向后兼容 v1；实现直接覆盖旧存档且缺少 migration 处理
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
