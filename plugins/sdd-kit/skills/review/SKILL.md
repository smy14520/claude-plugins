---
name: review
description: "Independent semantic audit of impl output against spec, task, wiki, and actual git diff. Runs AFTER impl reports DONE/DONE_WITH_CONCERNS. Read-only — never edits code, spec, or task. Reports with a strict 4-state machine (APPROVED / APPROVED_WITH_NOTES / NEEDS_REWORK / SPEC_DRIFT). Appends to task file's `## Review log` (separate from Status log). Must consult git diff; impl self-check is not a substitute. Primary invocation: `/sdd-kit:review <task-id-or-file>`."
disable-model-invocation: true
---

# Review — Independent Semantic Audit

Audit whether impl's DONE claim actually satisfies the spec. Impl's SelfCheck proves acceptance commands pass; review asks the harder question: **does what was built match what was specified?**

## Positioning in the 5-phase workflow

```
research → spec → task → impl → [review]
                           │        │
                           ▼        ▼
                       self-check   semantic audit
                       (acceptance  (spec ↔ diff ↔ wiki)
                        commands)
                           │        │
                           └─► status log    └─► review log
                               (in task file)    (same file, separate section)
```

Review is the **semantic safety net**. It:

- Reads spec + task + status log + **actual git diff** + (optional) wiki
- Compares implementation against spec semantics, not just acceptance
- Emits a 4-state review result
- **Does not** edit code, spec, or task
- **Does not** auto-invoke anything

## Why review is a separate skill (not part of impl)

Impl is scoped to see **only the task**. By construction, it cannot:

- Detect when the code silently drifts from spec's constraints
- Notice that acceptance passed but spec's non-functional requirements (SLO, security) are unmet
- Consult wiki gotchas relevant to this change
- Cross-check git diff for scope creep the task didn't mention

Running this broader check inside impl would pollute its "translator" role and pressure it toward either over-reaching or rubber-stamping. Separation keeps each skill honest.

## Three primitives

Match user intent; full procedures in [references/workflow.md](references/workflow.md).

### 🔍 Collect — gather audit context

Triggers: "review T-003", "audit impl 结果", "check if this matches spec".

> **Reasoning rhythm**: 🥐 **light**. Pure gathering: read files, run `git diff`, optionally query wiki. No judgments yet.

Procedure:

1. Resolve target: task ID (`T-003`) OR task file path OR recent DONE status line
2. Read the spec that the task derives from (`.claude/specs/<name>.md`)
3. Read the task entry + its full Status log history
4. Run `git diff <base>..HEAD -- <changed-files>` to see what impl actually changed
5. Optionally query wiki for relevant `[[gotcha-*]]` / `[[decision-*]]` pages (user-guided, not blanket)

### ⚖️ Judge — compare diff against spec

Triggers: after Collect. The heart of the skill.

> **Reasoning rhythm**: 🍞 **heavy**. Enable extended thinking / "think harder" when available. This is where the skill earns its token budget. Review in **fresh context** (new chat / subagent) whenever possible — reusing the context that wrote the code poisons the audit.

Procedure (detail in [references/workflow.md](references/workflow.md#judge)):

1. Check spec's **goal** is addressed by the diff (not just acceptance commands)
2. Check spec's **non-goals** are not violated (scope creep)
3. Check spec's **hard constraints** (rate limits, SLOs, invariants, security) are met or explicitly addressed in the diff
4. Check spec's **interface contract** matches what the code exposes
5. Cross-check against wiki `[[gotcha-*]]` pages that the diff's domain touches
6. Check the diff itself for: untested paths, missing error handling, scope creep beyond the task
7. Classify findings into one of the 4 states

### 📤 Report — emit review state

Triggers: after Judge.

> **Reasoning rhythm**: 🥐 **light**. Classification against fixed state machine; findings already produced in Judge.

Procedure (see [references/state-machine.md](references/state-machine.md)):

1. Classify into: APPROVED / APPROVED_WITH_NOTES / NEEDS_REWORK / SPEC_DRIFT
2. Append review line to task file's `## Review log` section (creating section if absent)
3. Emit structured summary to user with explicit next-step pointer
4. **If state is `SPEC_DRIFT`**: recommend returning to spec skill to reconcile, not re-running impl

## Four review states

Full definitions in [references/state-machine.md](references/state-machine.md). Quick reference:

| State | Meaning |
|-------|---------|
| **APPROVED** | Diff addresses spec's goal, respects non-goals, meets hard constraints. No reservations. |
| **APPROVED_WITH_NOTES** | Same as APPROVED, but reviewer flags minor concerns (style, edge case, follow-up suggestion). Not blocking. |
| **NEEDS_REWORK** | Diff has a semantic gap with spec (missing constraint, wrong behavior, untested required path). Impl must re-engage. |
| **SPEC_DRIFT** | Diff appears reasonable, but the spec itself is wrong/inconsistent/impossible. Bounces back to spec skill, NOT impl. |

## Review line format

Exact format, appended to the task file's `## Review log` section:

```
- [✓] T-003 (APPROVED) — 2025-04-18 16:40 — spec goal met; constraints OK; diff clean
- [~] T-004 (APPROVED_WITH_NOTES) — 2025-04-18 16:55 — passes but: hard-coded timeout 5s (spec said "configurable"); follow-up suggested
- [✗] T-005 (NEEDS_REWORK) — 2025-04-18 17:10 — spec requires rate-limiting 10/s; diff has no rate-limit middleware; src/webhooks/xhs-handler.ts:1-80 audited
- [!] T-006 (SPEC_DRIFT) — 2025-04-18 17:30 — spec says "use redis for idempotency"; codebase has no redis dep; spec is wrong or research is missing
```

Checkbox semantics:

- `[✓]` — APPROVED
- `[~]` — APPROVED_WITH_NOTES
- `[✗]` — NEEDS_REWORK
- `[!]` — SPEC_DRIFT

## Review log section (in task file)

Review log lives in the SAME task file as impl's Status log, but in a SEPARATE section:

```markdown
# <task file header>

## Tasks
...

## Status log
- [x] T-003 (DONE) — 2025-04-18 14:20 — all acceptance cmds green (3/3)

## Review log
- [✓] T-003 (APPROVED) — 2025-04-18 16:40 — spec goal met; constraints OK; diff clean
```

If `## Review log` section does not exist, review creates it below `## Status log`.

## Core rules

1. **Read-only** — review NEVER edits code, spec, task definition, or acceptance. Only appends to `## Review log`.
2. **Must read actual diff** — `git diff` is mandatory. Reading only the task's "acceptance passed" status line is NOT review; that's re-reading impl's self-check.
3. **Fresh context preferred** — if possible, invoke review in a new chat / subagent. Same-session review by the same actor that wrote the code is weakest form of audit.
4. **Scope: spec + diff + wiki** — do NOT re-read the research phase's raw notes; those are upstream of spec. If spec is unclear, that's a SPEC_DRIFT signal, not a review failure.
5. **No blessing without naming what was checked** — APPROVED must cite at least: goal ✓, non-goals ✓, constraints ✓, diff scope ✓. Empty "LGTM" is an anti-pattern.
6. **SPEC_DRIFT bounces to spec, not impl** — if the spec itself is wrong, rework must start at spec phase; re-running impl against a broken spec just re-creates the problem.
7. **One review per DONE / DONE_WITH_CONCERNS impl run** — each review line references the exact impl status line it audits.
8. **No auto-re-invocation** — review reports once and stops. User decides whether to bounce back to impl (for NEEDS_REWORK) or spec (for SPEC_DRIFT).

## Directory structure

Review does not create new directories. It writes only to:

```
.claude/tasks/<name>.tasks.md        # appends to ## Review log section
```

Optional (if user wants persistent multi-review trace):

```
.claude/reviews/<name>.review.md     # only on user request
```

## Initialization

If target task file does not exist: refuse with a clear message pointing to `task` skill.
If target task has no DONE/DONE_WITH_CONCERNS status line: refuse — "nothing to review yet".

## What this skill does NOT do

- Does NOT edit code — findings are reported, fixing is impl's job (next cycle)
- Does NOT edit spec — SPEC_DRIFT is a signal, not an action
- Does NOT run the acceptance commands again — impl's SelfCheck is trusted on the mechanical layer
- Does NOT re-decompose the task — task skill owns decomposition
- Does NOT block commit/merge — it only emits state; user acts

## When NOT to activate

- Impl has not yet reported DONE or DONE_WITH_CONCERNS for the task — nothing to audit
- Task is still NEEDS_CONTEXT or BLOCKED — resolve those first
- Ad-hoc impl with no task file — fall back to a lightweight review (read diff + user-stated goal)

## Anti-patterns

See [references/anti-patterns.md](references/anti-patterns.md). Quick list:

- Rubber-stamping APPROVED without naming what was checked
- Reading only the task file (not the git diff)
- Conflating "acceptance passed" with "spec satisfied"
- Editing code to "fix" what review found (that's impl's next-cycle job)
- Downgrading NEEDS_REWORK to APPROVED_WITH_NOTES to avoid a second impl pass
- Claiming APPROVED when hard constraints (SLO / security) were not checked against diff
- Using same chat context that wrote the code (self-review bias)
