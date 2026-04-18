---
status: open | closed
date: YYYY-MM-DD
topic: <topic-kebab-case>
---

<!-- 输出语言: 中文 -->

# Research: <topic>

## Question

<copy from question.md — one sentence>

## Key findings

- **<Finding 1 title>** — <one-line summary> → `refined/<note-1>.md`
- **<Finding 2 title>** — <one-line summary> → `refined/<note-2>.md`
- **<Finding 3 title>** — <one-line summary> → `refined/<note-3>.md`

## Open questions

(For spec to resolve — explicit list. If truly none, say so and explain how it was confirmed.)

- <open question 1>
- <open question 2>

## Ingest candidates

(Refined notes worth promoting to long-term wiki knowledge. User must run `wiki` ingest explicitly.)

- `refined/<note-a>.md` → proposed wiki type: `entity` / name: `<wiki-page-name>`
- `refined/<note-b>.md` → proposed wiki type: `gotcha` / name: `<wiki-page-name>`
- `refined/<note-c>.md` → proposed wiki type: `concept` / name: `<wiki-page-name>`

## Ephemeral (do NOT ingest)

(Refined notes scoped to this decision only, no reuse value.)

- `refined/<note-x>.md` — only relevant for this feeding decision
- `refined/<note-y>.md` — superseded by `<note-a>` in scope

## Next steps (for user to decide, not auto-triggered)

- Run `spec` skill to draft the design (open questions become decision points)
- Run `wiki` ingest for promoted candidates
- Or neither, revisit later
