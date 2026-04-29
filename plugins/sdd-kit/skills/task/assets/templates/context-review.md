# Legacy note: review context is now JSONL

New task packages use `context/review.jsonl` instead of `context/review.md`.

Review still reads package-local `prd.md`, `task.md`, `task.json`, and actual `git diff`; JSONL entries are short semantic audit hints.

```jsonl
{"at":"YYYY-MM-DDTHH:MM:SSZ","actor":"task","task_id":"T-001","kind":"constraint","source":"SRC-LOCAL-001","summary":"<review-only context packet; what semantic auditor must check against prd/task/diff>"}
```

Use `sdd-arbor add-context <name> --type review ...` to append entries.
