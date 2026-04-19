# Spec content contract

A spec is a dependable design contract. This file defines exactly what belongs in it and what does not.

## Required sections

A valid spec MUST contain ALL of these:

### 1. Frontmatter

```yaml
---
status: draft | accepted | revising | superseded
date: YYYY-MM-DD
tags: [<domain>, ...]          # optional
supersedes: <old-spec-name>    # optional
---
```

### 2. `# <Feature>` — title

Kebab-case topic, matches filename.

### 3. `## Goal` — ONE sentence

Imperative voice. Describes the outcome, not the path.

- ✅ "Provide an idempotent webhook endpoint for xhs customer events."
- ❌ "Implement xhs webhook integration with retry logic and signature verification."
- ❌ "Improve webhook handling."

### 4. `## Non-goals` — ≥ 2 explicit exclusions

What this spec will NOT do. Prevents scope creep.

- ✅ "Does NOT cover outbound xhs-to-customer messaging."
- ✅ "Does NOT migrate existing wechat webhook handler (separate spec)."
- ❌ (missing non-goals) — spec will drift

### 5. `## Hard constraints`

Numeric or binary where possible:

- Latency: p99 < 200ms
- Throughput: 500 req/s sustained
- Consistency: at-least-once delivery, idempotent per `event_id`
- Security: signature verified; clock skew tolerance ≤ 5 min
- Compatibility: must not break existing `/webhook/wechat` handler

No vague adjectives ("fast", "reliable", "scalable") without numeric backing.

### 6. `## Interface contract`

Exact inputs, outputs, error shapes:

- For HTTP: method, path, request body schema, response body schema, status codes
- For functions: signature, parameter types, return type, exceptions
- For events: topic, payload schema, ack protocol
- For config / constants: exact names AND exact values (URLs, enum lists, SLO numbers, feature-flag keys)

**Unknown concrete values** (a URL you don't know yet, an enum you haven't decided) MUST be written as `<TODO-DECIDE: specific question>`. Descriptions like "与 docs 保持一致" / "校准 XX" / "保持默认" are forbidden in place of exact values — they silently leak unresolved work to task and impl, where resolving them is expensive. See also Finalize step's marker grep.

Include an acceptance-criteria block:

```markdown
### Acceptance
- [ ] POST /webhook/xhs returns 200 within 200ms for valid signed request
- [ ] Returns 401 for invalid signature
- [ ] Returns 409 for replay (duplicate event_id within 24h)
- [ ] Metrics emit: counter `webhook.xhs.received`, histogram `webhook.xhs.latency`
```

### 7. `## Data / state design`

Which entities, tables, queues, caches are involved. State transitions if any.

- Tables touched: `xhs_events (id, event_id, payload, processed_at)`
- Cache keys: `xhs:replay:<event_id>` TTL 24h
- State machine: `pending → processed | failed`

Do NOT write full schema DDL (that lives in migrations). Write the *shape* of the data model.

### 8. `## Integration points`

Upstream / downstream dependencies:

- Upstream: xhs pushes webhooks to our `/webhook/xhs` endpoint
- Downstream: `customer-service-bus` topic receives normalized events
- Sibling: shares `signature-verifier` util with `[[wechat-webhook]]` (optional wikilink)

### 9. `## Test strategy`

How this spec will be verified:

- Unit: signature verification, idempotency key computation
- Integration: full webhook → db → event-bus roundtrip
- Replay test: same event_id twice, second returns 409
- Load: sustained 500 req/s for 10 min, p99 latency tracked

Do NOT write full test cases (those live in tests/); write the *categories* of testing and key scenarios.

## Forbidden sections

These NEVER appear in a spec:

### ❌ Alternatives / Rejected options

- "We considered HMAC vs RSA and chose HMAC because..." → belongs in `[[decision-hmac-vs-rsa-for-webhook]]` wiki page
- A spec reader should not need to see what was NOT chosen.

### ❌ Decision history / narrative

- "First we thought X, then we realized Y, so we pivoted to Z" → belongs in research `findings.md` or decision wiki page
- A spec is a statement, not a story.

### ❌ Problem statement / motivation essays

Motivation lives one level up (PRD, tickets, research). The spec assumes the reader knows why this is being built.

A one-line context note is fine:

> Context: replacing the manual ops workflow currently documented in `[[xhs-manual-ops-runbook]]`.

Longer motivation → move out of spec.

### ❌ Implementation steps / task breakdown

"Step 1: create table. Step 2: write handler. Step 3: add test." → that's what `task` skill produces. Spec describes the *what*, not the *how*.

### ❌ Discovery / exploration content

"Looking at how other teams do this, we found X..." → belongs in research

### ❌ Open questions

A finalized spec has zero open questions. If unresolved, spec status is `draft` or `revising`, not `accepted`.

## Length guideline

- Sweet spot: 100-250 lines
- Warning: > 400 lines (consider splitting)
- Minimum: ~80 lines (any shorter and you've probably skipped sections)

## Relationship to other artifacts

| Artifact | What it holds | Example |
|----------|---------------|---------|
| Spec | final "what will be built" | `.claude/specs/xhs-webhook.md` |
| Decision wiki page | "why this over that" | `.claude/wiki/hmac-vs-rsa-for-xhs.md` |
| Research findings | "what we explored" | `.claude/research/xhs-customer/findings.md` |
| Task file | "execution steps" | `.claude/tasks/xhs-webhook.tasks.md` |
| Code | actual implementation | `src/webhooks/xhs.ts` |

Each holds one concern. Do not merge them.

## Wikilink policy

- Spec MAY reference `[[entity-xxx]]`, `[[concept-xxx]]`, `[[decision-xxx]]` as background
- Wikilinks are READER HINTS, not required reading
- Spec must be fully understandable without following any wikilink
- If a concept is critical, inline a one-line summary + wikilink for "more"

Example:

> Reuses the `[[signature-verifier]]` util (signature verification with clock-skew tolerance; see wiki for implementation details).

## The "executor test"

A spec passes the content contract iff: a task/impl engineer reading ONLY this spec (no research, no wiki) can produce acceptance-compliant code without asking any further design question.

If they would need to ask "but what about X?", X is missing from the spec.
