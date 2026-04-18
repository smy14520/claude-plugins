# Status line reference

Append one line per Report to the task file's `## Status log` section.

## Formats (copy the right one)

### DONE

```
- [x] T-NNN (DONE) — YYYY-MM-DD HH:MM — <short fact-based note; acceptance cmds green N/N>
```

### DONE_WITH_CONCERNS

```
- [?] T-NNN (DONE_WITH_CONCERNS) — YYYY-MM-DD HH:MM — <concern summary>; <file:line or follow-up hint>
```

### NEEDS_CONTEXT

```
- [!] T-NNN (NEEDS_CONTEXT) — YYYY-MM-DD HH:MM — <ambiguity summary>; source: <spec §X or task <field>>
```

### BLOCKED

```
- [✗] T-NNN (BLOCKED) — YYYY-MM-DD HH:MM — <blocker summary>; unblock: <what needs to happen>
```

## Rules

1. **One line per state transition**. Multiple lines per task allowed (audit trail).
2. **Timestamp required**. Local time, ISO-ish format.
3. **Short** — under 150 chars after the `— `. Full detail goes in the user-visible summary, not the status line.
4. **Fact-based**. No "should" / "will" / "seems". Only observed state.
5. **Do NOT edit existing lines**. Append new ones.

## Examples (good)

```
- [x] T-001 (DONE) — 2025-04-18 10:30 — acceptance 3/3 green
- [x] T-002 (DONE) — 2025-04-18 11:15 — acceptance 2/2 green
- [?] T-003 (DONE_WITH_CONCERNS) — 2025-04-18 14:20 — retry uses fixed 3 tries no backoff; src/webhooks/xhs.ts:47
- [!] T-004 (NEEDS_CONTEXT) — 2025-04-18 15:05 — replay TTL 24h or 7d? spec §Constraints vs task acceptance disagree
- [✗] T-005 (BLOCKED) — 2025-04-18 15:30 — postgres 14 vs 15 mismatch; unblock: align env or rewrite migration
- [x] T-004 (DONE) — 2025-04-18 16:50 — user clarified TTL=24h, 2/2 green
- [x] T-005 (DONE) — 2025-04-18 17:30 — postgres upgraded to 15, migration applied, 1/1 green
```

## Examples (bad — do not write these)

```
- [x] T-003 (DONE) — should work                  # "should" = speculation
- [x] T-003 (DONE) — done                         # no fact
- [?] T-003 (DWC) — has concerns                  # what concerns?
- [✗] T-003 (BLOCKED) — can't do it               # unspecific
- [x] T-003 — 2025-04-18                          # missing state
```
