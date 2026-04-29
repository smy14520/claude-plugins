# Legacy note: impl context is now JSONL

New task packages use `context/impl.jsonl` instead of `context/impl.md`.

Each line should be a short JSON object:

```jsonl
{"at":"YYYY-MM-DDTHH:MM:SSZ","actor":"task","task_id":"T-001","kind":"constraint","source":"SRC-LOCAL-001","summary":"<implementation-only context packet; short, factual, task-local>"}
```

Use `sdd-arbor add-context <name> --type impl ...` to append entries.
