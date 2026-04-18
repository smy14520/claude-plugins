# Decomposition: strict-atomic vs lean

Two explicit modes. Pick per task file (not per session).

## Mode comparison

| Aspect | strict-atomic | lean |
|--------|---------------|------|
| Max size per task | ≤ 4h | ≤ 1 day |
| Deliverables per task | Exactly 1 | 1-3 related |
| Files touched per task | Typically 1-2 | Up to ~5 |
| Commit grain | 1 task = 1 commit | 1 task = 1-few commits |
| Good for | multi-agent / multi-person; parallel impl; long-lived work | solo dev; quick prototypes; time-boxed work |
| Ceremony | high (more tasks, explicit DAG) | lower (fewer tasks, implicit order) |
| Risk | over-decomposition for small work | tasks become too coarse to verify precisely |

## Choosing

### Pick strict-atomic when

- Multiple humans or agents will execute concurrently
- Work spans > 1 week (need stable handoff points)
- Critical feature where each unit needs independent review
- User explicitly wants parallelism

### Pick lean when

- Solo, 1-2 day effort
- Prototype / experiment where the plan may change
- Simple CRUD-style work where the seams are obvious
- Over-decomposition would add more ceremony than value

### Default

If user doesn't specify: **strict-atomic**. Err on the side of clear seams; coarse tasks are worse than too-many tasks.

## strict-atomic rules

1. Every task has **one** `deliverable:` entry (not "three files")
2. Every task has **one** verifiable acceptance (can be a command)
3. Estimates 0.5h – 4h
4. Shared modules are always separate tasks
5. Tests can be their own tasks OR bundled into the feature task — both acceptable; consistency within a file

### Example (strict-atomic)

```markdown
- id: T-003
  role: backend
  title: "Implement POST /webhook/xhs handler"
  deliverable: "src/webhooks/xhs-handler.ts"
  depends-on: [T-001, T-002]
  acceptance: |
    - file: src/webhooks/xhs-handler.ts exports handleXhsWebhook(req)
    - handler: returns 200 for signed requests, 401 for unsigned
    - no tests in this task (T-005 covers tests)
  estimate: 3h

- id: T-005
  role: test
  title: "Tests for /webhook/xhs handler"
  deliverable: "tests/webhooks/xhs-handler.test.ts"
  depends-on: [T-003]
  acceptance: |
    - run: pnpm test tests/webhooks/xhs-handler.test.ts passes
    - coverage: happy path + invalid signature + duplicate event_id
  estimate: 2h
```

## lean rules

1. A task can bundle related deliverables ("handler + its unit test")
2. Still has a single acceptance, but may be multi-step
3. Estimates up to 1 day (~6-8h)
4. Shared modules may be inlined into first consumer; promote out if a second consumer emerges

### Example (lean)

```markdown
- id: T-003
  role: backend
  title: "Implement POST /webhook/xhs (handler + tests)"
  deliverable: "src/webhooks/xhs-handler.ts + tests/webhooks/xhs-handler.test.ts"
  depends-on: [T-001, T-002]
  acceptance: |
    - file: src/webhooks/xhs-handler.ts exports handleXhsWebhook(req)
    - run: pnpm test tests/webhooks/xhs-handler.test.ts passes (≥ 3 cases: happy, invalid-sig, replay)
  estimate: 5h
```

## Decomposition heuristics (both modes)

### The "what can I verify independently?" test

If a deliverable cannot be verified without first verifying another, it depends on that one. That dependency becomes `depends-on`.

### The "single concern" test

A task should have one reason to change. If you can imagine two PRs for the same task, split.

### The "too-small" smell

If a task has:

- Estimate < 30 min
- Deliverable is literally one line ("add feature flag")
- No dependencies, no dependents

Consider inlining into the next task. Micro-tasks pile ceremony.

### The "too-big" smell

If a task has:

- Estimate > mode's max (4h atomic / 1 day lean)
- Deliverable is a list ("migrate X, rewrite Y, add Z")
- Multiple `notes:` about "also need to handle..."

Split.

## Common decomposition buckets

Derive tasks from these spec sections:

| Spec section | Typical tasks |
|--------------|---------------|
| Data / state design | migrations, seeds, schema tests |
| Interface contract | handler, controller, api client, validators |
| Constraints | rate-limiter, auth middleware, signature verifier |
| Integration points | producer, consumer, adapters |
| Test strategy | unit / integration / load test tasks |
| Observability | metrics emitters, log enrichers, dashboards |

Use these as a seed list; not every spec needs every bucket.

## How to decide task order

The dependency DAG emerges from what consumes what:

1. Storage first (migrations, schema) — nothing downstream works without it
2. Shared utilities next (signature verifier, HTTP client, etc.)
3. Core logic (handlers, domain services)
4. Integration (event producers / consumers)
5. Tests (either alongside #3 or after, per project convention)
6. Devops last (deploy config, feature flags) — unless blocking (e.g. secret must exist before code can run)

If you find yourself writing a task that references something "to be added later", that's a dependency. Declare it explicitly.

## Re-decomposition trigger

Initial task file was lean → impl gets stuck → reveals a hidden dependency → decompose that task further.

Allowed; do:

1. Change parent task `status: split`
2. Add new sub-tasks with fresh IDs, depends-on parent's dependencies
3. Impl picks up the new atomic tasks

Never silently edit the parent task; preserve the trail.
