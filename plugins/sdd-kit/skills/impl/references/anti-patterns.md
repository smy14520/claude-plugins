# Impl anti-patterns

Observed failure modes, many inherited from prior SDD tooling. Avoid all.

---

## 1. Claiming DONE without running acceptance

**Symptom**: status line says DONE; check reveals `pnpm test` was never run, or ran and failed, or ran on wrong path.

**Why wrong**: violates the core "no unverified claims" rule. Propagates false green.

**Fix**: SelfCheck step MUST execute every `acceptance:` entry. If a command can't be run (env issue), state is BLOCKED, not DONE.

---

## 2. Silent design decision to unblock

**Symptom**: task was ambiguous on retry count. Executor picked "3 tries" silently and marked DONE.

**Why wrong**: the choice is now invisible; future readers assume "3" was intended by the spec. Downstream decisions compound on the hidden guess.

**Fix**: STOP on ambiguity → NEEDS_CONTEXT with the specific question. Let user (or spec) decide. If urgency demands a guess, mark DONE_WITH_CONCERNS and explicitly name "chose 3 tries in absence of spec guidance".

---

## 3. BLOCKED masked as DONE_WITH_CONCERNS

**Symptom**: dependency unavailable, executor writes "stub" code that doesn't actually meet acceptance, marks DWC.

**Why wrong**: DWC means acceptance PASSED with concern. If acceptance didn't pass, it's BLOCKED (or NEEDS_CONTEXT).

**Fix**: DWC requires acceptance to actually pass. Stubs that fake acceptance are lying.

---

## 4. Acceptance modified to make it pass

**Symptom**: task says "pnpm test tests/xhs.test.ts passes". Test was failing. Executor changed the test (or the task's acceptance) to pass, then claims DONE.

**Why wrong**: acceptance is authoritative. Changing it defeats the contract.

**Fix**:

- If the test itself is wrong → that's a task-level issue, bounce NEEDS_CONTEXT
- If the implementation is wrong → fix impl, re-SelfCheck
- Never edit the task's `acceptance:` field from impl

---

## 5. Bundling cleanup into a task commit

**Symptom**: task T-003 was scoped to add one handler. Executor also refactored an unrelated file "while in there".

**Why wrong**: scope creep, review blast radius, dependency tangles, rollback complexity.

**Fix**: keep the task focused on its deliverable. Adjacent cleanup is a follow-up task.

---

## 6. "Running tests" without reading output

**Symptom**: status says DONE, but `pnpm test` output actually shows 2 failures (the executor skimmed the final "passed" line from a different test suite).

**Why wrong**: superficial SelfCheck.

**Fix**: SelfCheck means parse exit code + check the actual failure count in output. If in doubt, dump the output lines for user.

---

## 7. Auto-advancing to next task

**Symptom**: T-003 reported DONE, impl immediately starts T-004 without user input.

**Why wrong**: violates "single task, single report" principle. User may want to review diff, commit, hand off.

**Fix**: always stop after Report. User explicitly says "continue" / "next" to proceed.

---

## 8. Over-testing unrelated areas

**Symptom**: task acceptance says "test xhs.test.ts passes". Executor runs full test suite, one unrelated test fails, executor hangs on that.

**Why wrong**: acceptance scope is the task's scope. Unrelated failures are a separate concern.

**Fix**: run acceptance commands as written. If doing a broader sanity check reveals unrelated issues → note them as an observation, do NOT hold the task on them.

---

## 9. SelfCheck with `# it should work` comments instead of commands

**Symptom**: task had no runnable check in acceptance (because task skill didn't decompose it), so executor adds a comment like `// verified manually` and marks DONE.

**Why wrong**: unverifiable; no regression guard.

**Fix**: if task acceptance genuinely has no runnable check (e.g. "config value updated"), that acceptance is a file-state predicate — read the file and check it programmatically. If task truly requires manual confirmation, report DONE-PENDING-MANUAL and wait.

---

## 10. Using Claude's internal TaskCreate / TaskUpdate as the progress model

**Symptom**: impl uses the Claude-private task API for its own tracking, user sees nothing in `.claude/tasks/*.tasks.md`.

**Why wrong**: file-based task status is the user-visible source of truth. Internal tracking is ephemeral to the session.

**Fix**: always append to the task file's `## Status log`. Internal tools can be used but MUST mirror to the file.

---

## 11. Reusing a status line

**Symptom**: task T-003 failed BLOCKED; executor later retries, and EDITS the BLOCKED status line to DONE.

**Why wrong**: destroys audit trail.

**Fix**: append a new status line. Old line stays. See `state-machine.md` on multiple status lines per task.

---

## 12. Not surfacing test observations

**Symptom**: during SelfCheck, executor notices 3 pre-existing test failures in unrelated area. Says nothing.

**Why wrong**: lost signal. User doesn't know the project has broken tests.

**Fix**: in status summary, note: "Observation: project has N pre-existing test failures in area X (not this task's responsibility)". Let user decide.

---

## 13. Re-writing spec to match impl

**Symptom**: impl realized spec's latency constraint (p99 < 200ms) is unrealistic. Edited spec to say "300ms".

**Why wrong**: impl is not authoritative over spec. Spec is the contract.

**Fix**: if spec is wrong in impl's view, emit NEEDS_CONTEXT: "constraint p99<200ms seems unachievable on current infra, local test shows ~280ms. Please confirm spec or relax constraint." Let user amend spec.

---

## 14. Using "should" / "will" language in status lines

**Symptom**: status line says "DONE — should handle all cases correctly".

**Why wrong**: "should" is speculation. Status lines are facts.

**Fix**: use past-tense observed facts: "3/3 acceptance cmds green", "file exports match", "curl returned 200".

---

## 15. Skipping the concern documentation for DWC

**Symptom**: status line says DONE_WITH_CONCERNS but no concerns named.

**Why wrong**: the `[?]` signal is meaningless without the concern.

**Fix**: DWC status line MUST include the specific concern inline, or be rewritten as DONE (if no actual concern) or NEEDS_CONTEXT (if concern is actually a blocker).

---

## 16. Eager impl before task file is confirmed

**Symptom**: user asks for planning; impl jumps to coding.

**Why wrong**: cross-skill boundary violation. Impl consumes task, doesn't produce it.

**Fix**: if user hasn't confirmed a task (via task skill or ad-hoc confirmation), do NOT execute. Bounce to task skill or ask for ad-hoc confirmation first.
