# Task anti-patterns

Observed failure modes. Avoid all.

---

## 1. Tasks with wikilinks

**Symptom**: task file contains `[[entity-xxx]]` or similar.

**Why wrong**: task file must be self-sufficient. Executor reads ONE file. Wikilinks imply "go read the wiki", which forces context-switching and introduces hidden dependencies (wiki drift).

**Fix**: inline the necessary info into the task's `notes:` field (1-line summary). Or put the reference in the spec, not the task.

---

## 2. Tasks that require reading the spec

**Symptom**: task says "implement per spec section X" without spelling out what that means.

**Why wrong**: executor has to cross-read; spec may drift; any ambiguity becomes decision time during impl.

**Fix**: copy the relevant acceptance/constraint content into the task directly. Yes, this duplicates text with spec — that's intentional. Spec is authoritative; task is executable.

---

## 3. "Investigate X" tasks

**Symptom**: task like "investigate how the current signature verifier works" or "figure out the migration strategy".

**Why wrong**: investigation is research-phase. By the time we're at tasks, we should already know.

**Fix**: bounce back to research or spec. If the unknown is too small for full research, at least record it as a pre-task "spike" with a timebox + explicit exit criteria.

---

## 4. "Decide Y" tasks

**Symptom**: task like "decide which queue system to use" or "choose between HMAC and RSA".

**Why wrong**: decisions are spec-phase. Impl executor should never have to decide.

**Fix**: return to spec, resolve the decision, then re-decompose.

---

## 5. Over-decomposition for trivial work

**Symptom**: a 30-line PR becomes 4 tasks: `add type`, `add fn signature`, `fill fn body`, `add test`.

**Why wrong**: more ceremony than value. Each task's `notes` + `acceptance` overhead exceeds the actual work.

**Fix**: either use lean mode, or bundle into one task. A good test: if the PR would be one atomic commit by a human, it's one task.

---

## 6. Under-decomposition (kitchen-sink tasks)

**Symptom**: one task titled "implement the xhs webhook feature" with 20 files in `deliverable`.

**Why wrong**: no independent verification, no parallelism, no partial recovery on BLOCKED state.

**Fix**: split by acceptance criterion. Each independently-testable behavior becomes its own task.

---

## 7. Missing depends-on

**Symptom**: task touches a module that another task creates, but `depends-on` is empty or wrong.

**Why wrong**: executor runs task out of order, hits missing dep, BLOCKED. User has to manually reason about order.

**Fix**: scan each task's deliverable for references to files / modules / endpoints created by other tasks; populate `depends-on` accordingly.

---

## 8. Non-verifiable acceptance

**Symptom**: acceptance says "works correctly" / "looks good" / "handles edge cases".

**Why wrong**: impl can never claim DONE. User has to manually validate every task.

**Fix**: acceptance must be:

- A command (`pnpm test path/xxx.test.ts passes`)
- A file-state check (`src/xxx.ts exports fn<T>(…): U`)
- An HTTP call result (`curl -X POST /y returns 200 with {...}`)
- A binary predicate a human or script can execute

---

## 9. Renumbering IDs

**Symptom**: someone re-orders tasks, IDs get renumbered, impl status lines now reference wrong IDs.

**Why wrong**: destroys the trail from `.claude/tasks/foo.tasks.md` status lines and any external tracker.

**Fix**: IDs are append-only. Move tasks by reordering bullets (markdown order is presentation; ID is identity). Never reissue.

---

## 10. Auto-advancing to impl

**Symptom**: at end of decomposition, task skill starts writing code.

**Why wrong**: violates "阶段独立". User may want to review, hand off, or defer.

**Fix**: end with a summary + pointer "to impl: run `impl` skill with task file `<path>`".

---

## 11. Tasks that reference external state implicitly

**Symptom**: task says "add handler for new endpoint". Which endpoint? From where?

**Why wrong**: executor has to guess / re-derive from spec.

**Fix**: every task must name the concrete target (path, file, class, function) explicitly in its title or deliverable.

---

## 12. Mixed-mode task file

**Symptom**: file starts strict-atomic, then a few lean tasks appear (bundled concerns, ~1 day size).

**Why wrong**: inconsistent mental model; reviewers can't predict granularity; retro becomes noisy.

**Fix**: pick mode per file, not per task. If mid-plan you realize you need a different mode, that's signal to restart the file with the right mode.

---

## 13. Shared modules as a giant leaf node

**Symptom**: one `shared` task titled "utilities" with 10 deliverables.

**Why wrong**: defeats the point of shared extraction. Each "utility" is independently consumed; bundling forces artificial coupling.

**Fix**: one shared task per utility. If truly a bundle, that's not "shared" — it's a library and needs its own spec.

---

## 14. Tasks without a clear `deliverable:`

**Symptom**: deliverable says "improvements to X" or "refactor Y".

**Why wrong**: "improvement" is not a verifiable artifact.

**Fix**: deliverable must name a concrete target + change type:

- ✅ `src/service/xhs.ts: extract validateSignature() from handle()`
- ❌ `improvements to service/xhs.ts`

---

## 15. Re-opening DONE tasks silently

**Symptom**: impl found a bug; task skill (or user) edits the original task and marks it "revised".

**Why wrong**: loses the audit trail of what was originally DONE vs what changed.

**Fix**: add a new task (`T-020 fix regression in T-003`), with `depends-on: [T-003]`. Do not mutate completed tasks.
