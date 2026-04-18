---
name: spec
description: "Use this skill when the user wants to produce a dependable implementation spec for a feature or change. Trigger phrases: '写 spec X', '定方案 X', '设计 X 的实现方案', 'spec 一下 X', 'draft the spec for X', 'nail down the design for X'. Produces `.claude/specs/<name>.md` — a single-file contract covering goal, non-goals, interface, constraints, data/state, integration, test strategy. The spec strictly excludes decision history, rejected alternatives, and discovery narrative (those either go into `[[decision-xxx]]` wiki pages or stay in research). Task skill consumes this spec; impl executes against it. Does NOT auto-trigger task skill."
---

# Spec — Dependable Design Contract

Produce a single-file spec at `.claude/specs/<name>.md` that the task skill can decompose and the impl skill can execute against without re-deciding anything.

## Positioning in the 4-phase workflow

```
research → [spec] → task → impl
            ↓
            └─── may reference wiki for prior art (read-only, user-guided)
```

Spec is the **decision gate**. Open questions end here; ambiguity ends here. After spec, downstream phases are execution, not discovery.

- **Input**: user intent + optional research `findings.md` + optional wiki context (user-guided queries)
- **Output**: one `.claude/specs/<name>.md`
- **Ban**: decision history, rejected alternatives, discovery narrative (they belong in `[[decision-xxx]]` wiki pages, not here)

## Three primitives

Match user intent; full procedures in [references/workflow.md](references/workflow.md).

### 🎯 Frame — goal, non-goals, constraints

Triggers: "开始写 spec X", "spec 一下 X", "定方案 X".

Procedure (detail in `references/workflow.md#frame`):

1. Name the spec (kebab-case, topic-named, not dated)
2. Read `.claude/research/<topic>/findings.md` if exists and user references it
3. Establish: goal (one sentence) / non-goals (≥2) / hard constraints
4. Write skeleton `spec.md` from [assets/templates/spec.md](assets/templates/spec.md)

### ⚖️ Decide — resolve open questions

Triggers: during drafting, whenever the spec has unresolved `<TODO-DECIDE: ...>` markers.

Procedure:

1. Enumerate open questions (from research or newly surfaced)
2. For each, present options to user; let user choose (one roundtrip per decision, do not bundle)
3. Record each accepted choice **as a flat statement** in the spec
4. If user wants rationale preserved, offer: "要不要把这个决策的来龙去脉 ingest 为 `[[decision-<name>]]` wiki 页面？spec 本身不保留决策史。"
5. Do NOT write rejected alternatives into the spec

### ✅ Finalize — seal the spec

Triggers: "spec 定稿", "finalize the spec", user confirms all open questions resolved.

Procedure:

1. Scan spec for remaining `<TODO-DECIDE>` or `<TBD>` — must be zero
2. Apply content-contract check (see `references/content-contract.md`):
   - No decision narrative
   - No alternatives listed
   - No process history ("first we thought... then we realized...")
3. Set frontmatter `status: accepted`, `date: today`
4. Emit closing summary with pointer to next step (task skill or direct impl)
5. Do NOT invoke task skill

## Directory structure

```
.claude/specs/
├── <feature-a>.md      # one spec per feature/change, topic-named
├── <feature-b>.md
└── archive/            # optional, for superseded specs
    └── <feature-a>-v1.md
```

Naming:

- kebab-case topic name, no dates, no version suffix
- Versioning via frontmatter `status: superseded`, move to `archive/` if needed

## Core rules

1. **One spec = one contract** — a spec describes ONE feature or change. Multi-feature specs must be split.
2. **No decision history** — the spec is "what we will build", not "how we got here". History lives in `[[decision-xxx]]` wiki pages, explicitly ingested.
3. **No alternatives listed** — if the reader needs to see options considered, that is a decision-page concern, not a spec concern.
4. **Executor-ready** — a task/impl engineer reading this spec should need zero additional context to act. If they would need to re-decide something, the spec has an unresolved decision.
5. **Constraints are explicit** — rate limits, SLOs, invariants, security properties: state them directly, not by reference.
6. **Wikilinks are optional hints** — spec MAY link to `[[entity-xxx]]` or `[[concept-xxx]]` for background, but must not depend on wiki existing. A wikilink is a reader aid, not a dependency.
7. **No auto-advance** — after finalization, the skill stops. Task skill is a separate invocation.

## Initialization

If `.claude/specs/` does not exist, create it silently on first use.

Per spec: create `.claude/specs/<name>.md` from [assets/templates/spec.md](assets/templates/spec.md).

## What this skill does NOT do

- Does not gather new raw material — use `research` for that
- Does not decompose into tasks — use `task` for that
- Does not write code — use `impl` for that
- Does not automatically read / merge research — user must reference research explicitly (`"基于 research findings 写 spec"`)
- Does not ingest anything into wiki — ingest is explicit via `wiki` skill

## When NOT to activate

- User asks a direct implementation question (no spec needed for a trivial change)
- User is still exploring options (use `research` first)
- User is already mid-impl and is adjusting course (spec amendment is fine; creating a new spec mid-flight is probably over-engineering)

## Anti-patterns

See [references/anti-patterns.md](references/anti-patterns.md). Quick list:

- Keeping rejected alternatives "for reference"
- Writing the spec as a decision narrative ("we first considered X, then Y, and chose Z")
- Gluing multiple features into one spec
- Leaving `<TODO-DECIDE>` markers in an accepted spec
- Auto-triggering task skill at end
- Writing constraints as vague goals ("should be fast") instead of numeric SLOs
