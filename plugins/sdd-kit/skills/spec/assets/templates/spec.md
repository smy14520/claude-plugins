---
status: draft
date: YYYY-MM-DD
tags: [<domain>, ...]
supersedes: <old-spec-name>   # optional, remove if N/A
---

<!-- 输出语言: 中文 -->

# <feature-name>

## Goal

<ONE sentence, imperative voice. Describes the outcome, not the path.>

## Non-goals

- <explicit exclusion 1>
- <explicit exclusion 2>

## Hard constraints

- <numeric constraint, e.g. p99 latency < 200ms>
- <binary constraint, e.g. signature verified per RFC xxx>
- <compatibility constraint, e.g. must not break existing /webhook/wechat handler>

## Interface contract

### Inputs / Outputs

<For HTTP: method, path, request schema, response schema, status codes>
<For functions: signature, param types, return type, exceptions>
<For events: topic, payload schema, ack protocol>

### Acceptance

- [ ] <verifiable happy path acceptance>
- [ ] <verifiable failure path acceptance>
- [ ] <idempotency / replay if relevant>
- [ ] <observability: metric / log / trace that must emit>

## Data / state design

<Tables, queues, caches involved. State machine if any. Shape, not full DDL.>

- Tables touched: `<table> (fields...)`
- Cache keys: `<pattern>` TTL `<value>`
- State transitions: `<from> → <to>` on `<event>`

## Integration points

- Upstream: <who calls this>
- Downstream: <what this calls>
- Sibling: <shares util X with [[sibling-entity]]>

## Test strategy

- Unit: <key scenarios>
- Integration: <end-to-end flow>
- <Load / replay / failure-injection if relevant>

## Background (optional, ≤ 5 lines)

<Only if a reader truly needs one-line context. Link to [[decision-*]] pages for rationale. Delete this section if not needed.>

<!--
  Reminders (delete after drafting):
  - No decision history here. Rationale → [[decision-xxx]] wiki page.
  - No alternatives listed. Options comparison → decision page or research.
  - No implementation steps. Task breakdown → task skill.
  - Non-goals must have ≥ 2 items.
  - Constraints must be numeric or binary.
  - Acceptance must cover happy path, failure path, idempotency, observability.
-->
