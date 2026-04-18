---
name: task
description: "Use this skill to decompose a spec (or a confirmed goal) into an atomic execution plan that a downstream executor can consume WITHOUT re-deciding anything. Trigger phrases: '拆任务 X', '把 spec X 变成任务', '生成 task 计划', 'break down spec X into tasks', 'plan the work for X'. Produces `.claude/tasks/<name>.tasks.md` — a list of atomic tasks with ID, role, dependencies, deliverable, acceptance. Supports two modes: strict-atomic (every task ≤ 4h, single commit) and lean (coarser tasks). Task files MUST NOT contain `[[wikilinks]]` — they must be self-sufficient. Does NOT auto-trigger impl."
---

# Task — Atomic Execution Plan

Decompose a spec into tasks an executor can run without decision-making. One task = one atomic deliverable + one verifiable acceptance.

## Positioning in the 4-phase workflow

```
research → spec → [task] → impl
                    ↓
                    └─── executor reads ONLY this file
```

Task is the **decomposition + ordering** phase. It:

- Reads a spec (`.claude/specs/<name>.md`) OR an in-session goal
- Splits into atomic units with stable IDs
- Identifies shared / common modules (prevents duplicate code across agents)
- Orders via explicit `depends-on` DAG
- Optionally tags each task with a role (backend/frontend/data/devops/shared) for future multi-agent split
- **Does not** execute; **does not** re-decide

## Four primitives

Match user intent; full procedures in [references/workflow.md](references/workflow.md).

### 🔨 Decompose — split into atomic tasks

Triggers: "拆任务 X", "把 spec X 变成任务", "plan X".

Procedure (detail in `references/workflow.md#decompose`):

1. Resolve input: `.claude/specs/<name>.md` OR in-session description
2. Ask user: strict-atomic vs lean mode (see [references/decomposition.md](references/decomposition.md))
3. Split spec into units. Each unit = one deliverable
4. Assign stable IDs (`T-001`, `T-002`, …)
5. Populate required fields per unit (see content-contract)

### 🧱 Identify shared — surface common modules

Triggers: during decomposition, or explicit "有哪些是公共模块".

Procedure:

1. Scan tasks for repeated concerns (e.g. 3 tasks all talk to the same HTTP client)
2. Extract a `shared-module` task for each
3. Make consumer tasks `depends-on` the shared-module task
4. Warn user if extraction count is high (signal: may be over-decomposing)

### 🔗 Order — build the dependency DAG

Triggers: during decomposition, or explicit "排一下依赖".

Procedure:

1. For each task, determine `depends-on: [IDs]`
2. Check for cycles → if any, report + block finalization
3. Emit the dependency graph (text tree or mermaid, no fancy)

### 🏷️ Assign role — optional multi-agent annotation

Triggers: user says "按角色分", "tag roles", or when multi-agent impl is anticipated.

Procedure:

1. Suggest role per task: `backend` | `frontend` | `data` | `devops` | `shared` | `test`
2. User confirms/edits
3. Roles are advisory, not binding — current impl runs single-agent

## Directory structure

```
.claude/tasks/
├── <spec-name>.tasks.md      # matches spec name when derived from one
└── <ad-hoc-name>.tasks.md    # for direct decomposition without a spec
```

File naming:

- If derived from spec: same kebab-case name + `.tasks.md` suffix
- If ad-hoc: user-provided or inferred kebab-case name + `.tasks.md`

## Core rules

1. **No wikilinks in task files** — task execution plans MUST be self-sufficient. Executor reads this file alone. Wiki references belong in spec, not task.
2. **No decisions in tasks** — each task has a concrete deliverable and verifiable acceptance. If a task has "decide how to X", it is a spec-phase concern, not a task. Bounce back to spec.
3. **Stable IDs** — once assigned, task IDs never change. Inserting new tasks picks a fresh ID, not a renumber.
4. **One commit ideal** — strict-atomic mode: each task produces exactly one deliverable (one file, one endpoint, one migration). Lean mode: relaxed to "one logical unit" but still verifiable.
5. **Acceptance is verifiable** — each task must name: (a) file(s) that will change, (b) command(s) to verify (`pnpm test`, `curl …`, etc.).
6. **Shared modules go first** — if task T-004 depends on shared T-001, T-001 must be scheduled ahead.
7. **No auto-advance** — after task file is written, skill stops. Impl is a separate invocation.

## Mode selection (strict-atomic vs lean)

Ask user explicitly. Defaults:

- **Strict-atomic** (default for multi-person or multi-agent impl):
  - Each task ≤ 4h, single commit, single deliverable
  - Higher ceremony, better for parallelism
- **Lean** (default for solo quick impl):
  - Tasks can span 1 day, multiple files
  - Lower ceremony, faster to write, less parallel-friendly

Details in [references/decomposition.md](references/decomposition.md).

## Initialization

If `.claude/tasks/` does not exist, create it silently on first use.

## What this skill does NOT do

- Does not execute tasks — use `impl` skill
- Does not re-decide design questions — bounce back to `spec`
- Does not read wiki — task files are self-sufficient, wiki context stays in spec
- Does not track progress / mutate task status — that is `impl`'s job via status lines
- Does not auto-trigger impl

## When NOT to activate

- User wants to fix a 1-liner bug — skip task, go direct to impl
- Spec is incomplete (`status: draft`, has `TODO-DECIDE`) — finalize spec first
- User is still deciding scope — use `spec` skill
- Previous task file exists and is current — read it, do not redo

## Anti-patterns

See [references/anti-patterns.md](references/anti-patterns.md). Quick list:

- Tasks that require the executor to read the spec
- Tasks with `[[wikilinks]]`
- Tasks that say "investigate X" (that's research)
- Tasks with "decide Y" (that's spec)
- Over-decomposition for trivial work (3 tasks for a 30-line PR)
- Missing `depends-on` declarations (executor has to guess order)
- Non-verifiable acceptance ("looks good")
