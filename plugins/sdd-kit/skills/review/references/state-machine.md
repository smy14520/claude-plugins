# The 4-state review machine

Review reports one of exactly four states. This file gives definitions, exit criteria, and transition rules.

> **Parallel to impl's state machine**, but different dimensions. Impl measures "did my task acceptance pass". Review measures "does the diff semantically satisfy the spec".

---

## APPROVED

**Meaning**: the diff addresses spec's goal, respects non-goals, meets hard constraints, matches interface contract. No reservations.

### Exit criteria (ALL must hold)

- Goal coverage: can point to diff hunk(s) that deliver the goal
- Non-goals: diff does not reach into explicitly-excluded scope
- Hard constraints: every constraint has evidence in diff (code or test)
- Interface contract: exports match spec
- Wiki cross-check: no relevant gotcha is contradicted (or none apply)
- Diff hygiene: no untested required paths, no error-path gaps, no scope creep

### Forbidden reasons to claim APPROVED

- "Acceptance commands passed, looks good" → that's impl's SelfCheck, not review
- "I skimmed the diff and it feels right" → must cite file:line evidence
- "No gotcha pages exist for this domain" → ok to skip wiki, but say so explicitly

### Review line example

```
- [✓] T-003 (APPROVED) — 2025-04-18 16:40 — goal met; non-goals ✓; rate-limit mw ✓ (src/mw/rate-limit.ts:12); HMAC on raw body ✓; diff clean
```

---

## APPROVED_WITH_NOTES

**Meaning**: semantic layer is correct, but reviewer flags minor concerns that are not blocking.

### When to use

- Minor scope creep that's harmless (e.g. unrelated typo fix in same commit)
- Hard-coded value where spec implied configurable (soft constraint)
- Missing optional test coverage for a non-critical path
- Wiki gotcha partially addressed but not fully
- Style / naming that departs from project convention in a minor way

### Required output

MUST include a concerns block naming:

- What the concern is (one sentence per concern)
- Where it lives (file:line)
- Severity rationale (why minor, not blocking)
- Optional: suggested follow-up task

### Forbidden

- Using APPROVED_WITH_NOTES to hide a real hard-constraint gap: that's NEEDS_REWORK
- Vague concerns ("could be cleaner") without specifics
- Stacking 5+ minor concerns without asking "should this actually be NEEDS_REWORK?"

### Review line example

```
- [~] T-004 (APPROVED_WITH_NOTES) — 2025-04-18 16:55 — core correct; timeout hard-coded 5s (spec said "configurable") src/webhooks/xhs-handler.ts:34; suggest follow-up
```

### Follow-up pattern

For substantive concerns, suggest a follow-up task:

```
建议新建 T-0NN: "Make xhs webhook timeout configurable via env"
  role: backend
  depends-on: [T-004]
  estimate: 30min
```

User decides whether to file it.

---

## NEEDS_REWORK

**Meaning**: diff has a semantic gap with spec. Impl must re-engage.

### When to use

- Hard-constraint gap (rate limit missing, SLO unaddressed, security check absent)
- Spec goal not fully delivered (e.g. handler returns 500ms for 95% but spec said 99%)
- Non-goal violated (scope creep into excluded domain)
- Required path has no test coverage
- Interface contract mismatch (exports wrong, signature different)
- Wiki gotcha directly contradicted without rationale

### Required output

MUST specify:

- **Gap**: one-sentence summary of what's missing or wrong
- **Evidence**: file:line pointing to the code that demonstrates the gap (or "no code addresses this")
- **Spec reference**: which spec section / constraint was not met
- **Suggested fix direction**: a hint, not a prescription (reviewer is not impl)
- **Blast radius**: does this require re-decomposition, or is it a localized patch?

### Forbidden

- Using NEEDS_REWORK to enforce personal taste ("I'd have done X instead")
- Claiming NEEDS_REWORK on things the spec did not require
- Demanding refactor beyond what's needed to close the gap
- Writing the actual fix in the review (that's impl's next cycle)

### Review line example

```
- [✗] T-005 (NEEDS_REWORK) — 2025-04-18 17:10 — spec §3 requires rate-limit 10/s per client; diff has no rate-limit middleware (scanned src/webhooks/ and src/mw/); acceptance cmd did not exercise burst scenario
```

### Resolution path

User options:

1. Re-run `/sdd-kit:impl T-00X` with the review findings as context
2. Re-decompose the task if the gap is too large for one cycle
3. Drop the task if the gap reveals the feature should be deferred

---

## SPEC_DRIFT

**Meaning**: diff appears reasonable, but the spec itself is wrong, inconsistent, or impossible. Bounces back to spec skill, NOT impl.

### When to use

- Spec mandates a dependency that doesn't exist in the codebase
- Spec's hard constraint is physically impossible (e.g. p99 < 1ms for a network call)
- Spec contradicts itself (§2 says X, §4 says not-X)
- Spec assumes architecture that no longer applies (stale spec vs current code)
- Spec's acceptance command references infrastructure that was deprecated
- Research phase was skipped and spec is making guesses that reality invalidates

### Required output

MUST specify:

- **Drift**: one-sentence summary of what the spec got wrong
- **Evidence**: quote the offending spec line + point to codebase reality
- **Impact**: what parts of the impl are still valid, what need to be reconsidered
- **Suggested path**: which spec section to rework; whether research is needed

### Forbidden

- Using SPEC_DRIFT as escape hatch when impl is actually at fault (that's NEEDS_REWORK)
- Claiming SPEC_DRIFT on spec ambiguity (ambiguity → impl should have emitted NEEDS_CONTEXT; if impl guessed, that's NEEDS_REWORK on impl)
- SPEC_DRIFT that just says "spec could be clearer" — must cite a concrete contradiction or impossibility

### Review line example

```
- [!] T-006 (SPEC_DRIFT) — 2025-04-18 17:30 — spec §4 requires redis for idempotency; no redis dep in package.json; codebase uses in-memory Map in src/store/dedup.ts; spec predates architecture change
```

### Recovery path

User options:

1. `/sdd-kit:spec <name>` to revise the drifted section
2. `/sdd-kit:research <topic>` if the drift reveals a knowledge gap
3. Keep the impl's partial work if it's salvageable for the revised spec
4. Abandon this task entirely if the spec premise is fundamentally broken

**Do NOT re-run impl first.** Impl against a broken spec just re-creates the bug.

---

## State transition rules

### Forward transitions (allowed)

```
impl (DONE / DONE_WITH_CONCERNS)  ──►  Collect  ──►  Judge  ──►  APPROVED
                                                         │
                                                         ├──►  APPROVED_WITH_NOTES (+ concerns block)
                                                         │
                                                         ├──►  NEEDS_REWORK (+ gap block)  ──►  back to impl
                                                         │
                                                         └──►  SPEC_DRIFT (+ drift block)  ──►  back to spec
```

### Rework re-review

```
NEEDS_REWORK  ──(impl re-runs, reports DONE)──►  new review cycle, new review line appended
SPEC_DRIFT    ──(spec revised, task possibly re-decomposed, impl re-runs)──►  new review cycle
APPROVED      ──(no action by default)──►  stays APPROVED
APPROVED_WITH_NOTES  ──(follow-up task filed)──►  stays APPROVED_WITH_NOTES (original)
```

### Forbidden transitions (HARD RULES)

- ❌ `APPROVED ← NEEDS_REWORK` silently (never "on second thought, good enough" without re-examining evidence)
- ❌ `APPROVED ← SPEC_DRIFT` silently (spec drift does not dissolve by ignoring it)
- ❌ `APPROVED_WITH_NOTES` with 5+ concerns (at that point, re-classify as NEEDS_REWORK)
- ❌ Editing earlier review lines (append-only; new line per re-review)

Each re-entry to review appends a NEW review line; the old line stays for audit.

---

## Multiple review lines per task

A task may accumulate multiple review lines over re-reviews:

```
- [✗] T-003 (NEEDS_REWORK) — 2025-04-18 17:10 — rate-limit missing
- [✓] T-003 (APPROVED) — 2025-04-18 18:40 — re-reviewed after impl rework, rate-limit now at src/mw/rate-limit.ts:12
```

This is the audit trail. Do NOT collapse into one line.

---

## Relation to impl's state machine

Review and impl have orthogonal state machines. A task can be:

| Impl state | Review state | Meaning |
|-----------|--------------|---------|
| DONE | not yet reviewed | impl complete, awaiting audit |
| DONE | APPROVED | ready to ship |
| DONE | APPROVED_WITH_NOTES | ready to ship with minor follow-up |
| DONE | NEEDS_REWORK | impl thought it's done; review disagrees → back to impl |
| DONE | SPEC_DRIFT | impl did its job; spec is wrong → back to spec |
| DONE_WITH_CONCERNS | APPROVED | concerns were acceptable to reviewer |
| DONE_WITH_CONCERNS | NEEDS_REWORK | concerns were NOT acceptable |
| NEEDS_CONTEXT | (cannot review) | impl not complete |
| BLOCKED | (cannot review) | impl not complete |

---

## Escalation rule

If a task has cycled `NEEDS_REWORK → impl → NEEDS_REWORK` 3+ times:

```
⚠️ T-003 has entered NEEDS_REWORK 3 times in review.
Suggestion:
  - Task may be mis-scoped (re-decompose via /sdd-kit:task)
  - Or spec may be under-specified (return to /sdd-kit:spec with findings as feedback)
  - Or review criteria may be too strict for task's actual scope (reconcile with user)

Do not keep cycling review → impl → review without addressing the upstream.
```
