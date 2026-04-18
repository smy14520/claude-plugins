---
name: impl
description: "Execute a task (or ad-hoc goal) as actual code changes. Picks a task from `.claude/tasks/<name>.tasks.md`, writes code to meet its acceptance, runs its own acceptance commands (self-check, not semantic review), reports with a strict 4-state machine (DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED). Never claims DONE without passing `acceptance:` commands. Never silently makes design decisions — ambiguity forces NEEDS_CONTEXT. Semantic audit against spec is the review skill's job, not impl's. Appends status line to the task file. Works without a task file too. Primary invocation: `/sdd-kit:impl <task-id-or-file>`."
disable-model-invocation: true
---

# Impl — Task Executor with 4-State Reporting

Execute tasks as code. Run your own acceptance commands before claiming DONE. Never silently downgrade BLOCKED into DONE.

## Positioning in the 5-phase workflow

```
research → spec → task → [impl] → review
                           ↓          ↑
                           └─ self-check only (mechanical)
                              semantic audit lives in review skill
```

Impl is the **execution** phase. It:

- Reads the task (from file or in-session)
- Writes code to satisfy acceptance
- Runs its own acceptance commands (**self-check**, mechanical)
- Reports a status in the 4-state machine
- **Does not** change the task list; **does not** make design decisions
- **Does not** perform semantic audit against spec — that is the `review` skill's job

## Four primitives

Match user intent; full procedures in [references/workflow.md](references/workflow.md).

### 🎯 Pick — select task

Triggers: "实施 T-003", "执行下一个 task", "run next task".

> **Reasoning rhythm**: 🥐 **light**. Selection + eligibility check, mechanical.

Procedure:

1. Locate `.claude/tasks/<file>.tasks.md` (user specifies OR scan most-recent)
2. Read task list + existing status log
3. Pick next eligible task: `depends-on` all in `DONE` state, task itself not yet done/blocked
4. Confirm with user: "下一个: T-003 `<title>` — estimate 3h. 开始？"

If no task file: fall back to ad-hoc mode (`references/workflow.md#ad-hoc`).

### 🔨 Execute — write code

Triggers: after Pick, or immediate start.

> **Reasoning rhythm**: 🥐 **light**. You are a translator, not a designer — task `deliverable` + `acceptance` are the contract. If the translation is not mechanical, that is a sign of ambiguity and you should emit `NEEDS_CONTEXT`, not think harder. Save tokens here; heavy semantic reasoning belongs to the `review` skill (a separate invocation, different context).

Procedure:

1. Read the task's `deliverable` + `acceptance` + `notes`
2. Read spec if needed (only for context, not for re-decision)
3. Write code aimed at acceptance criteria
4. If ambiguity arises → STOP and emit NEEDS_CONTEXT (see state-machine.md)

### ✅ SelfCheck — run the task's own acceptance commands

Triggers: after Execute, always before reporting DONE.

> **Reasoning rhythm**: 🥐 **light, disciplined**. Mechanical: run commands, read output, check exit codes. The discipline is refusing to interpret failures as "probably fine" — not heavy reasoning. Heavy semantic reasoning belongs to the `review` skill.

> **Scope**: SelfCheck verifies only what the task's `acceptance:` block specifies. It does NOT cross-check against spec semantics, does NOT inspect whether the code truly solves the user-level problem. Those are `review` skill concerns.

Procedure:

1. Run every command in task's `acceptance:`
2. Capture exit code + relevant output
3. Any failure → do NOT claim DONE
4. SelfCheck scope matches `acceptance:` — no extra, no less

### 📤 Report — emit state

Triggers: after SelfCheck, or on BLOCKED / NEEDS_CONTEXT.

> **Reasoning rhythm**: 🥐 **light**. Classification against a fixed 4-state machine; no new reasoning beyond what SelfCheck produced.

Procedure (see [references/state-machine.md](references/state-machine.md) for definitions):

1. Classify into: DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED
2. Append status line to task file's `## Status log` section
3. Emit structured summary to user with next-task suggestion (no auto-advance)
4. **If state is `DONE_WITH_CONCERNS` or `BLOCKED`**: emit a wiki-ingest **suggestion** (never auto-ingest) — see [references/workflow.md#report-wiki-ingest-suggestion](references/workflow.md). The suggestion includes a proposed page name, type, and a content draft derived from the concern/blocker. User must explicitly run `/sdd-kit:wiki` to ingest.

## Four states

Full definitions in [references/state-machine.md](references/state-machine.md). Quick reference:

| State | Meaning |
|-------|---------|
| **DONE** | All acceptance commands passed, no known compromises |
| **DONE_WITH_CONCERNS** | Acceptance passed, but executor noticed tech debt / compromise / non-ideal path. MUST document concern. |
| **NEEDS_CONTEXT** | Ambiguity or missing info blocks completion; executor refuses to decide. MUST specify what context is needed. |
| **BLOCKED** | Environment / dependency / external factor prevents proceeding. MUST name blocker. |

## Directory structure

```
.claude/tasks/
└── <name>.tasks.md      # ← appended status log lives inside this file

.claude/impl-logs/       # optional, created on first long-running impl
└── <name>.log.md        # cumulative session trace (multi-task runs)
```

## Status line format

Exact format, appended to the task file's `## Status log` section:

```
- [x] T-003 (DONE) — 2025-04-18 14:20 — all acceptance cmds green (3/3)
- [?] T-004 (DONE_WITH_CONCERNS) — 2025-04-18 14:50 — passed but: retry logic uses fixed 3 tries, no backoff; see note in src/webhooks/xhs-handler.ts:42
- [!] T-005 (NEEDS_CONTEXT) — 2025-04-18 15:10 — spec ambiguous on replay window: 24h vs 7d? acceptance doesn't specify
- [✗] T-006 (BLOCKED) — 2025-04-18 15:30 — db migration fails: local postgres 14 vs expected 15; need devops to align
```

Checkbox semantics:

- `[x]` — DONE
- `[?]` — DONE_WITH_CONCERNS
- `[!]` — NEEDS_CONTEXT
- `[✗]` — BLOCKED

## Core rules

1. **No unverified claims** — NEVER emit DONE without running `acceptance:` commands. "Should work" = NEEDS_CONTEXT, not DONE.
2. **No silent state downgrade** — BLOCKED does not become DONE because "I figured out a workaround". A workaround that deviates from acceptance is DONE_WITH_CONCERNS. A workaround that meets acceptance is DONE.
3. **No design decisions** — if the task has ambiguity, emit NEEDS_CONTEXT. Do not invent a choice.
4. **No task mutation** — impl does not edit the task's title, deliverable, or acceptance. Only appends to status log.
5. **One task at a time** — complete + report before picking the next. Prevents half-done state.
6. **SelfCheck = acceptance** — if acceptance says "passes test X", you run X. Don't run less (false DONE). Don't run more (scope creep, unrelated failures). Don't second-guess the spec — if spec itself seems wrong, emit NEEDS_CONTEXT or let `review` flag SPEC_DRIFT.
7. **Ad-hoc mode follows same rules** — even without a task file, same 4-state reporting.
8. **No auto-advance to next task** — impl reports one task and stops, unless user explicitly says "continue".

## Initialization

If `.claude/tasks/` does not exist: impl cannot run task-mode, only ad-hoc.
If `.claude/impl-logs/` does not exist and user wants multi-session trace: create on first impl.

## What this skill does NOT do

- Does not modify spec (spec is authoritative; if spec is wrong, return NEEDS_CONTEXT, or let `review` flag SPEC_DRIFT)
- Does not modify task definition (only appends status)
- Does not skip SelfCheck "because it's obvious"
- Does not perform semantic audit against spec (that is the `review` skill's job)
- Does not bundle multiple tasks into one commit / one status line
- Does not auto-advance after DONE — user decides
- Does not auto-invoke `review` — user decides when to audit

## When NOT to activate

- Task file has unresolved upstream BLOCKED on a dependency — resolve that first
- User is still in research/spec phase — use prior skills
- No code change is actually needed (pure design discussion) — just answer

## Anti-patterns

See [references/anti-patterns.md](references/anti-patterns.md). Quick list:

- Claiming DONE without running `acceptance:` commands
- Merging BLOCKED into DONE_WITH_CONCERNS without naming the blocker
- Silently making a design choice to unblock (should be NEEDS_CONTEXT)
- Editing the task's acceptance to pass
- "Running tests" without reading their output
- Bundling unrelated cleanup into a task commit
- Performing semantic audit against spec within SelfCheck (that belongs to `review`)
