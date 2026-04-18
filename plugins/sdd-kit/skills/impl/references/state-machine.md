# The 4-state machine

Impl reports one of exactly four states. This file gives definitions, exit criteria, and transition rules.

---

## DONE

**Meaning**: the task is complete. All acceptance passes. No known compromises or deferred concerns.

### Exit criteria (ALL must hold)

- Every command in `acceptance:` executed and returned success
- Every file-state predicate in `acceptance:` verified
- No known deviation from spec or task constraints
- Code is self-consistent (no dangling TODOs left for this task)

### Forbidden reasons to claim DONE

- "Acceptance passes locally" → did you run all of them? Actually? Including the HTTP one?
- "Close enough" → DONE_WITH_CONCERNS instead
- "Everything except the test, which I'll add later" → not DONE
- "Passed in my head" → not DONE until commands actually ran

### Status line example

```
- [x] T-003 (DONE) — 2025-04-18 14:20 — 3/3 acceptance green
```

---

## DONE_WITH_CONCERNS

**Meaning**: acceptance passes, but the executor made a compromise worth surfacing.

### When to use

- Used a workaround that meets acceptance but isn't the clean solution
- Skipped an optional improvement mentioned in task notes
- Introduced a small tech debt the future reader should know about
- Deviated from project convention in a minor way (documented inline)

### Required output

MUST include a concerns block naming:

- What the compromise is (one sentence)
- Where it lives in the code (file:line)
- Recommended follow-up (optional: new task ID suggestion)

### Forbidden

- Using DONE_WITH_CONCERNS to hide a real failure: that's BLOCKED or NEEDS_CONTEXT
- "Concerns: code could be cleaner" without specifics (not actionable)

### Status line example

```
- [?] T-003 (DONE_WITH_CONCERNS) — 2025-04-18 14:50 — passed but retry uses fixed 3 tries, no backoff; src/webhooks/xhs-handler.ts:42
```

### Follow-up pattern

For substantive concerns, suggest a follow-up task:

```
建议新建 T-0NN: "Add exponential backoff to xhs retry"
  role: backend
  depends-on: [T-003]
  estimate: 1h
```

User decides whether to file it.

---

## NEEDS_CONTEXT

**Meaning**: executor hit an ambiguity or missing info that forces a design decision. Refuses to guess.

### When to use

- Spec says X, task says Y, they contradict
- Acceptance references a file/command that doesn't exist
- A concrete value is missing (e.g. TTL, retry count) that affects behavior
- Two reasonable implementations exist and task doesn't choose
- Required upstream dependency has undefined behavior

### Required output

MUST specify:

- **Blocked at**: one-sentence summary of what's ambiguous
- **Needed**: the specific question that would unblock
- **Source of ambiguity**: where in spec / task the ambiguity lives
- **Suggested resolution**: what change to spec or task would unblock
- **Code state**: "no code changes committed" OR "partial: <what's in>"

### Forbidden

- Using NEEDS_CONTEXT to avoid reading the spec more carefully
- Claiming NEEDS_CONTEXT on decisions already made in spec (re-read, don't ask)
- Silently making the choice and marking DONE — that's the core failure mode to avoid

### Status line example

```
- [!] T-003 (NEEDS_CONTEXT) — 2025-04-18 15:10 — spec ambiguous on replay window: 24h vs 7d? acceptance says 24h, spec says 'align with wechat'
```

### Resolution path

User options:

1. Clarify in-session → impl consumes clarification, re-runs task
2. Update spec → re-finalize spec, re-decompose if needed, re-run impl
3. Drop / descope task → mark task `status: dropped`
4. Defer → leave NEEDS_CONTEXT, come back later

---

## BLOCKED

**Meaning**: environment or external factor prevents the task, unrelated to design ambiguity.

### When to use

- Dependency not installed, missing binary
- External service unreachable (DB, API, queue)
- Migration fails for infrastructure reason (version mismatch, missing extension)
- Permission / auth issue at machine level
- Upstream task still `NEEDS_CONTEXT` or `BLOCKED` (this task can't proceed)

### Required output

MUST specify:

- **Blocker**: one-sentence summary
- **Symptoms**: exact error message(s)
- **Tried**: any recovery steps attempted
- **Unblock path**: what needs to happen externally (who / what)
- **Code state**: "no code changes committed" OR "partial: <what's in>"

### Forbidden

- Using BLOCKED to avoid verifying (if you didn't run the command, you don't know it's blocked)
- Silent workaround that evades the blocker (that's DONE_WITH_CONCERNS at best, but more likely NEEDS_CONTEXT)
- Claiming BLOCKED for design issues (that's NEEDS_CONTEXT)

### Status line example

```
- [✗] T-003 (BLOCKED) — 2025-04-18 15:30 — postgres 14 vs 15 schema mismatch; migration requires 15; local is 14
```

### Recovery path

User options:

1. Fix environment → re-run task
2. Rewrite to work with current env (new decision: run spec / task again)
3. Defer task, skip ahead to other eligible tasks
4. Drop task

---

## State transition rules

### Forward transitions (allowed)

```
(start)  ───────►  Execute  ───────►  Verify  ───────►  DONE
                      │                 │
                      │                 ├──► DONE_WITH_CONCERNS (+ concerns doc)
                      │                 │
                      │                 └──► BLOCKED (acceptance cmd fails for env reason)
                      │
                      ├────────────►  NEEDS_CONTEXT (ambiguity found)
                      │
                      └────────────►  BLOCKED (env issue during execute)
```

### Rework transitions (re-open)

```
NEEDS_CONTEXT  ──(user clarifies)──►  re-Execute
BLOCKED        ──(env fixed)──────►  re-Execute
DONE_WITH_CONCERNS  ──(follow-up filed)──►  stays DONE_WITH_CONCERNS
DONE           ──(regression found)──►  file NEW task, do NOT revise T-003
```

### Forbidden transitions (HARD RULES)

- ❌ `DONE ← BLOCKED` silently (never "figured out a workaround, now it's DONE" without explicit re-verify)
- ❌ `DONE ← NEEDS_CONTEXT` silently (never "just guessed at an answer and moved on")
- ❌ `DONE ← DONE_WITH_CONCERNS` (concerns don't dissolve; they require follow-up)

Each re-entry to a task appends a NEW status line; the old line stays for audit.

---

## Multiple status lines per task

A task may accumulate multiple status lines over re-runs:

```
- [!] T-003 (NEEDS_CONTEXT) — 2025-04-18 15:10 — replay window ambiguity
- [✗] T-003 (BLOCKED) — 2025-04-18 15:40 — fixed ambiguity, now postgres version issue
- [x] T-003 (DONE) — 2025-04-18 16:30 — env fixed, 3/3 acceptance green
```

This is the audit trail. Do NOT collapse into one line.

---

## Escalation rule

If a task has cycled through NEEDS_CONTEXT or BLOCKED 3+ times:

```
⚠️ T-003 has entered NEEDS_CONTEXT/BLOCKED 3 times.
Suggestion:
  - The task may be mis-scoped (re-decompose via task skill)
  - Or the spec may have a deeper ambiguity (return to spec skill)
  - Or the environment fundamentally doesn't fit the design (return to research)

Do not keep retrying without addressing the upstream.
```
