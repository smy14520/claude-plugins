# Spec anti-patterns

Observed failure modes. Avoid all.

---

## 1. The rationale dump

**Symptom**: spec contains multi-paragraph justifications for every design choice.

**Why wrong**: a spec is a contract, not an essay. Executors don't need to re-derive the logic; they need to know what to build.

**Fix**: move rationale to `[[decision-xxx]]` wiki pages. Spec states the outcome only.

---

## 2. Preserved alternatives

**Symptom**: spec has a section "Alternatives considered" listing rejected options.

**Why wrong**: rejected options are noise at execution time. They also tempt second-guessing during impl.

**Fix**: the option comparison lives in a decision wiki page (or research findings). Spec carries only the accepted choice.

---

## 3. Narrative spec

**Symptom**: spec reads like a story — "First we tried X. Then we hit Y. So we changed to Z."

**Why wrong**: history is not contract. Narrative doubles the reading time and adds no actionable info.

**Fix**: rewrite as flat statements. "Uses Z because of Y constraint." (If even this causal clause drifts toward narrative, drop it and let the `[[decision-xxx]]` page carry the why.)

---

## 4. Vague constraints

**Symptom**: "should be fast", "should be secure", "should be reliable".

**Why wrong**: unactionable. Task/impl cannot know when the constraint is met.

**Fix**: numeric or binary. `p99 < 200ms`, `signature verified per RFC xxx`, `at-least-once delivery`.

---

## 5. Multi-feature spec

**Symptom**: one spec covers "xhs webhook + admin dashboard + migration from wechat".

**Why wrong**: acceptance becomes unclear; task decomposition tangles across features; review becomes all-or-nothing.

**Fix**: one spec per feature. Sibling specs can reference each other via `supersedes` / `related-specs` frontmatter.

---

## 6. Implementation steps in spec

**Symptom**: spec contains "Step 1: create migration. Step 2: write handler. Step 3: add test."

**Why wrong**: that's the task skill's job. Spec is "what" not "how".

**Fix**: describe the end state (data model, interface, invariants). Let `task` decompose.

---

## 7. Leaking research into spec

**Symptom**: "Looking at how wechat does it..." / "After exploring 3 options..."

**Why wrong**: research content in spec blurs the separation. Future readers have to filter "is this a finding or a commitment?"

**Fix**: research findings stay in `.claude/research/<topic>/findings.md`. Spec extracts only the resulting commitment.

---

## 8. Empty non-goals

**Symptom**: non-goals section missing or says "none".

**Why wrong**: scope will drift. Every non-trivial feature has neighbors it could spill into.

**Fix**: force ≥ 2 explicit non-goals. Examples: "does NOT replace existing wechat handler", "does NOT handle outbound messages", "does NOT introduce a new queue system".

---

## 9. Accepting spec with `<TODO-DECIDE>`

**Symptom**: spec status = `accepted` but grep finds `TODO-DECIDE` or `TBD`.

**Why wrong**: downstream impl will hit the undefined spot and have to re-decide, violating the "executor doesn't decide" principle.

**Fix**: Finalize step MUST block on any unresolved marker. Never auto-accept.

---

## 10. Auto-advancing to task

**Symptom**: at Finalize, the spec skill invokes task skill and starts decomposing.

**Why wrong**: violates "阶段独立" principle. User may want to:

- Pause for review
- Skip task (for a small spec, go direct to impl)
- Hand spec to another human / agent

**Fix**: Finalize ends with a summary + *suggestion* of next step. User explicitly runs task skill when ready.

---

## 11. Duplicating wiki content

**Symptom**: spec copies full content from `[[entity-xxx]]` or `[[concept-xxx]]` into itself.

**Why wrong**: wiki becomes non-authoritative; spec bloats; changes drift.

**Fix**: link to the wiki page, inline a 1-line summary for context:

> Reuses `[[signature-verifier]]` (HMAC-SHA256 with configurable clock-skew tolerance).

---

## 12. Under-scoped acceptance

**Symptom**: acceptance criteria only cover happy path.

**Why wrong**: impl will ship without handling errors, replays, edge cases; tasks won't cover them.

**Fix**: acceptance MUST cover:

- Happy path
- At least one validation failure path
- Idempotency / replay (if relevant)
- Observability (metric/log/trace that must emit)

---

## 13. Over-specifying implementation

**Symptom**: spec says "use Redis with LUA script, table must be PostgreSQL with BRIN index".

**Why wrong**: unless the choice is a hard constraint (e.g. team standard), it over-binds impl. Impl may find a better option.

**Fix**: specify the *capability* ("idempotency store with 24h TTL"), not the tech choice, unless the tech is itself a hard constraint.

---

## 14. Spec without test strategy

**Symptom**: `## Test strategy` section missing or says "will be tested".

**Why wrong**: impl will underspecify tests; acceptance won't be verifiable.

**Fix**: list test categories (unit / integration / load / manual) and name the key scenarios each must cover.
