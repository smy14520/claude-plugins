# Review anti-patterns

Observed failure modes. Avoid all.

---

## 1. Rubber-stamp APPROVED

**Symptom**: review line says APPROVED with nothing more than "LGTM" or "looks good".

**Why wrong**: violates "no blessing without naming what was checked". Makes review worthless as audit trail — a future reader cannot reconstruct what was verified.

**Fix**: APPROVED MUST cite at least: goal ✓, non-goals ✓, constraints ✓ (named), diff scope ✓. Short is fine; nameless is not.

---

## 2. Reading only the task file, not the git diff

**Symptom**: reviewer reads task's `acceptance:` and Status log line "DONE — 3/3 pass", then marks APPROVED without running `git diff`.

**Why wrong**: that's just re-reading impl's own self-check. Review's whole purpose is independent cross-check against actual code.

**Fix**: `git diff <base>..HEAD -- <files>` is mandatory. No review without diff inspection.

---

## 3. Conflating "acceptance passed" with "spec satisfied"

**Symptom**: "All acceptance commands returned exit 0, so APPROVED."

**Why wrong**: acceptance commands are what the task skill specified as the executable check. They may be incomplete (task missed a constraint), or may test the wrong thing (test bug). Semantic satisfaction of spec is a higher bar.

**Fix**: treat acceptance success as **necessary but not sufficient**. Explicitly cross-check spec's hard constraints against the diff, independent of whether acceptance tested them.

---

## 4. Editing code to fix what review found

**Symptom**: review finds a missing rate-limit, then in the same turn edits `src/mw/rate-limit.ts` to add one and marks APPROVED.

**Why wrong**: review is read-only by design. Code changes belong to impl's next cycle, where they get their own SelfCheck and (later) their own review line. Fixing in review destroys the independence that gives review its value.

**Fix**: emit NEEDS_REWORK with the gap description. Let user invoke `/sdd-kit:impl T-00X` for the fix.

---

## 5. Downgrading NEEDS_REWORK to APPROVED_WITH_NOTES to avoid another cycle

**Symptom**: reviewer found a missing rate-limit (hard constraint) but marks APPROVED_WITH_NOTES "suggest follow-up task" to avoid sending user back to impl.

**Why wrong**: hard-constraint gaps are blocking by definition. Classifying them as "notes" falsifies the audit trail and lets a real bug ship.

**Fix**: hard constraint missing = NEEDS_REWORK. Period. If the user finds the cycle time annoying, the answer is better task decomposition, not softer review.

---

## 6. Claiming APPROVED without checking hard constraints against diff

**Symptom**: review line says APPROVED, but reviewer never explicitly verified the rate-limit / SLO / HMAC / idempotency / retry-policy requirements.

**Why wrong**: these are the constraints most likely to be silently unmet — they don't always fail acceptance tests, they just degrade production quality or security.

**Fix**: for every hard constraint in spec, explicitly cite file:line evidence in the review (either "✓ at X:Y" or "✗ not addressed").

---

## 7. Using the same chat context that wrote the code (self-review)

**Symptom**: user runs `/sdd-kit:impl T-003` and then immediately `/sdd-kit:review T-003` in the same chat. The model that just wrote the code now reviews itself.

**Why wrong**: context bias — the model has anchored on "this is the right answer" during impl and cannot neutrally audit.

**Fix**: invoke review in a new chat / subagent. If unavoidable, flag it in the review line: `note: same-session review (self-audit); consider second opinion`.

---

## 8. Vague NEEDS_REWORK

**Symptom**: review says NEEDS_REWORK with reason "code is not clean".

**Why wrong**: impl cannot act on it. No file:line, no spec section, no concrete gap. Looks like a review but is really a vibe.

**Fix**: NEEDS_REWORK must specify: Gap (one sentence) / Evidence (file:line) / Spec reference (§X) / Suggested fix direction.

---

## 9. Claiming SPEC_DRIFT when impl is actually at fault

**Symptom**: impl silently guessed at an ambiguity and produced odd code. Review calls SPEC_DRIFT.

**Why wrong**: the drift is in impl's interpretation, not the spec. Real SPEC_DRIFT is spec-level contradiction or impossibility.

**Fix**:

- If impl guessed where spec was clear → NEEDS_REWORK on impl
- If impl guessed where spec was ambiguous → NEEDS_REWORK on impl (should have emitted NEEDS_CONTEXT), plus hint to spec that clarification is worthwhile
- If spec itself is wrong / impossible / self-contradictory → SPEC_DRIFT

---

## 10. Writing the actual fix inside review findings

**Symptom**: review's "findings" section contains a full code snippet showing how to fix the gap, not just a direction hint.

**Why wrong**: review over-reaches. It prescribes implementation, which is impl's domain. If review is that specific, maybe the reviewer should have run impl themselves; but they didn't, so the prescription is untested.

**Fix**: findings describe what's missing and point to spec+codebase context. Let impl decide how to fix in its next cycle.

---

## 11. Reviewing a task still in NEEDS_CONTEXT / BLOCKED

**Symptom**: user asks to review T-005 even though impl reported NEEDS_CONTEXT.

**Why wrong**: there's no DONE state to audit. Whatever partial code exists is incomplete by impl's own admission.

**Fix**: refuse with pointer to resolve impl state first. Never "review" incomplete work.

---

## 12. Re-editing an earlier review line

**Symptom**: task T-003 got NEEDS_REWORK, impl fixed it, reviewer EDITS the original NEEDS_REWORK line to APPROVED.

**Why wrong**: destroys audit trail. Future reader cannot see the rework cycle happened.

**Fix**: append a NEW review line. Old line stays.

---

## 13. Stacking many minor concerns instead of asking "is this NEEDS_REWORK?"

**Symptom**: review is APPROVED_WITH_NOTES but lists 7 concerns across 4 files.

**Why wrong**: beyond a few notes, the signal flips — the diff has systemic issues that warrant another impl cycle, not a "follow-up suggestion".

**Fix**: threshold of ~3 minor concerns. Above that, re-classify as NEEDS_REWORK with "diff needs multiple corrections" as the gap.

---

## 14. Over-reading: re-litigating spec in review

**Symptom**: review finds the implementation correct per spec, but reviewer uses review to argue the spec is suboptimal ("we should have chosen a different algorithm").

**Why wrong**: review audits impl against spec, not spec against the reviewer's preferences. That's a spec-skill conversation.

**Fix**: if spec seems wrong but diff implements it correctly → APPROVED and separately recommend user revisit spec. Not SPEC_DRIFT (which is contradiction/impossibility), just design debt worth a later look.

---

## 15. Silently skipping wiki cross-check

**Symptom**: review never mentions wiki. Maybe checked, maybe not — unclear.

**Why wrong**: wiki gotchas exist precisely to catch repeat pains. Silent skip loses institutional memory.

**Fix**: explicitly say either "wiki: checked [[gotcha-X]], [[gotcha-Y]] — no contradictions" or "wiki: skipped — no pages in this domain yet".
