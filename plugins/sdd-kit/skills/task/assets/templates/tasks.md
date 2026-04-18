---
spec: <spec-name or null if ad-hoc>
mode: strict-atomic | lean
date: YYYY-MM-DD
status: draft | confirmed | in-progress | done
---

# Tasks: <feature-name>

<!--
  Task file contract (enforced):
  - NO wikilinks. Self-sufficient file.
  - NO decisions. Every task is execution only.
  - IDs are append-only. Never renumber.
  - Every acceptance is a command or binary predicate.
-->

## Summary

- Mode: <strict-atomic | lean>
- Total tasks: <N>
- Total estimate: <hours>
- Critical path: <T-xxx → T-yyy → T-zzz = Nh>

## Dependency graph

```
T-001 (data)
  ↳ T-003 (backend)
       ↳ T-005 (test)
T-002 (shared)
  ↳ T-003 (backend)
  ↳ T-004 (backend)
T-007 (devops, standalone)
```

## Tasks

- id: T-001
  role: data
  title: "Migration: create xhs_events table"
  deliverable: "db/migrations/NNNN_create_xhs_events.sql"
  depends-on: []
  acceptance: |
    - file: db/migrations/NNNN_create_xhs_events.sql exists
    - run: `pnpm db:migrate` applies without error
    - schema: xhs_events(id, event_id UNIQUE, payload, processed_at, created_at)
  estimate: 1h
  notes: ""

- id: T-002
  role: shared
  title: "Signature verifier utility"
  deliverable: "src/lib/signature-verifier.ts"
  depends-on: []
  acceptance: |
    - file: src/lib/signature-verifier.ts exports verifyHmac(payload, sig, secret, maxSkewMs)
    - run: `pnpm test src/lib/signature-verifier.test.ts` passes
    - covers: valid sig → true; invalid → false; clock skew > 5min → false
  estimate: 2h
  notes: ""

- id: T-003
  role: backend
  title: "POST /webhook/xhs handler"
  deliverable: "src/webhooks/xhs-handler.ts"
  depends-on: [T-001, T-002]
  acceptance: |
    - file: src/webhooks/xhs-handler.ts exports handleXhsWebhook(req): Response
    - on valid signed request: writes to xhs_events, returns 200
    - on invalid signature: returns 401
    - on duplicate event_id: returns 409 (idempotency)
    - emits metric: webhook.xhs.received
  estimate: 3h
  notes: "Uses T-002 verifier. Reads secret from env XHS_WEBHOOK_SECRET."

# ... add more tasks with appended IDs ...

## Status log

(Impl skill appends here as tasks progress. Do NOT edit manually.)

<!-- format: `- [x] T-NNN (STATE) — YYYY-MM-DD HH:MM — note` -->
<!-- STATE ∈ { DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED } -->
