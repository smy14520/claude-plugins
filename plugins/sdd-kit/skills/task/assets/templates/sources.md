# Legacy note: sources are now JSONL

New task packages use `context/sources.jsonl` instead of `context/sources.md`.

Each source entry should be one JSON object:

```jsonl
{"id":"SRC-LOCAL-001","type":"local-file","location":"src/...:12-48","title":"<title>","why_it_matters":"<why this source matters for the package>"}
```

Use `sdd-arbor add-context <name> --type sources ...` to append entries.
