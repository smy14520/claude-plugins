<!--
Review line format. Append to task file's ## Review log section.

Checkbox semantics:
  [✓] — APPROVED
  [~] — APPROVED_WITH_NOTES
  [✗] — NEEDS_REWORK
  [!] — SPEC_DRIFT

Format:
  - <checkbox> <TASK-ID> (<STATE>) — <YYYY-MM-DD HH:MM> — <terse evidence summary>

The summary should name WHAT was checked, not just declare a verdict.
Include file:line pointers for any concrete evidence.
-->

## 示例

### APPROVED（通过）

```
- [✓] T-003 (APPROVED) — 2025-04-18 16:40 — goal met; non-goals ✓; rate-limit mw at src/mw/rate-limit.ts:12; HMAC on raw body src/webhooks/xhs-verify.ts:8; diff clean
```

### APPROVED_WITH_NOTES（有轻微问题）

```
- [~] T-004 (APPROVED_WITH_NOTES) — 2025-04-18 16:55 — core correct; timeout hard-coded 5s (spec §2 said "configurable") src/webhooks/xhs-handler.ts:34; follow-up suggested
```

### NEEDS_REWORK（存在具体缺陷）

```
- [✗] T-005 (NEEDS_REWORK) — 2025-04-18 17:10 — spec §3 requires rate-limit 10/s per client; no rate-limit middleware in diff; scanned src/webhooks/ and src/mw/; acceptance cmd didn't exercise burst
```

### SPEC_DRIFT（规格说明有误）

```
- [!] T-006 (SPEC_DRIFT) — 2025-04-18 17:30 — spec §4 mandates redis for idempotency; no redis dep in package.json; codebase uses in-memory Map src/store/dedup.ts:18; spec predates arch change
```

### 同会话自审注意事项

```
- [✓] T-003 (APPROVED) — 2025-04-18 16:40 — <summary>; note: same-session review, consider second opinion
```

### 临时任务（无规格说明）

```
- [✓] T-adhoc-1 (APPROVED) — 2025-04-18 16:40 — diff matches user-stated goal; hygiene ✓; note: ad-hoc lightweight review (no spec)
```
