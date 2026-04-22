<!--
Review line format. Append to task file's ## Review log section.

Checkbox semantics:
  [✓] — APPROVED
  [~] — APPROVED_WITH_NOTES
  [✗] — NEEDS_REWORK
  [!] — BRAINSTORM_DRIFT
-->

## 示例

### APPROVED（通过）

```
- [✓] T-003 (APPROVED) — 2025-04-18 16:40 — brainstorm goal met; task scope respected; diff clean
```

### APPROVED_WITH_NOTES（有轻微问题）

```
- [~] T-004 (APPROVED_WITH_NOTES) — 2025-04-18 16:55 — core correct; timeout hard-coded 5s though task notes imply configurable; src/webhooks/xhs-handler.ts:34
```

### NEEDS_REWORK（存在具体缺陷）

```
- [✗] T-005 (NEEDS_REWORK) — 2025-04-18 17:10 — task acceptance requires burst scenario; diff lacks rate-limit handling; scanned src/webhooks/ and src/mw/
```

### BRAINSTORM_DRIFT（上游收敛文档有误）

```
- [!] T-006 (BRAINSTORM_DRIFT) — 2025-04-18 17:30 — brainstorm mandates redis for idempotency; no redis dep in package.json; current codebase uses in-memory Map
```
