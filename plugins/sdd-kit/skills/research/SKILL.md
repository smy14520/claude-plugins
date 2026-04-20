---
name: research
description: "Bounded exploration of a topic before committing to a spec/design. Produces `.claude/research/<topic>/` with raw materials, refined notes, and a `findings.md` summarizing discoveries + open questions + wiki-ingest candidates. Does NOT make design decisions (spec skill's job) and does NOT auto-advance. Invoke only on explicit user request (e.g. '用 research skill 调研 <topic>')."
---

# Research — Bounded Exploration

Produce a focused exploration record under `.claude/research/<topic>/`. Separate raw collection from refined distillation. Hand control back to the user; do not auto-advance.

## Positioning in the 4-phase workflow

```
[research] → spec → task → impl
     ↓
     └─── user selectively ingests into wiki (user-triggered only)
```

This skill owns the **exploration** phase only. It:

- Gathers raw material (codebase reads, docs, URLs, user-provided artifacts)
- Distills into short refined notes
- Surfaces open questions the spec must resolve
- **Does not** make architectural choices or commit to a design
- **Does not** auto-trigger `spec`

Research output is **ephemeral context**. Only items the user explicitly promotes become wiki knowledge.

## Four primitives

Match user intent; full procedures in [references/workflow.md](references/workflow.md).

### 🎯 Scope — frame the question

Triggers: "调研 X", "研究一下 X", "想做 X 先探索".

Procedure (detail in `references/workflow.md#scope`):

1. Restate the question in one sentence
2. List what is IN scope (2-4 items)
3. List what is explicitly OUT of scope (prevents bloat)
4. Name the decisions this research is feeding into (not the decisions themselves)
5. Write `question.md` from [assets/templates/question.md](assets/templates/question.md)

### 📥 Collect — gather raw material

Triggers: "收集 X 的资料", "看一下代码里 X 怎么做的", user pastes docs/URLs.

Procedure:

1. Accept raw inputs (pasted docs, URLs, screenshots, code dumps) → `raw/`
2. Scan codebase for relevant entry points → extract minimal quotes, save as `raw/codebase-<area>.md`
3. For URL-based inputs, follow the tool matrix, completeness rules, and failure handling in [references/data-collection.md](references/data-collection.md). Save to `raw/ext-<name>.md` (or per-tab / per-page variants per that reference). **A single `curl`-style attempt that fails and gives up is an anti-pattern** — the fallback ladder must be exhausted before declaring a URL unretrievable.
4. **Do not distill yet**. Raw is raw.

### 🔍 Refine — distill into focused notes

Triggers: "整理一下", "把收集到的提炼一下".

Procedure:

1. For each distinct finding, write one short `refined/<topic>.md` (≤ 80 lines)
2. Each refined note has: what I found / where I found it / why it matters / open question it raises
3. Discard raw material that did not contribute to any refined note (do not keep noise)
4. Apply template [assets/templates/finding-note.md](assets/templates/finding-note.md)

### 📤 Propose — surface findings + ingest candidates

Triggers: "总结一下 research", "research 完了", "可以结束研究了".

Procedure:

1. Write `findings.md` from [assets/templates/findings.md](assets/templates/findings.md)
2. List key findings (linked to `refined/` notes)
3. List open questions (for spec to resolve)
4. List **wiki-ingest candidates**: "以下发现若要沉淀成长期知识，建议 ingest" — do not auto-ingest
5. Emit closing summary; **do not** invoke spec skill

## Directory structure

```
.claude/research/<topic>/
├── question.md                  # scope + out-of-scope + feeding decisions
├── raw/                         # collected as-is, minimal processing
│   ├── codebase-<area>.md       # quotes from code with file:line refs
│   ├── ext-<source>.md          # external material summaries
│   └── user-input-YYYY-MM-DD.md # pasted artifacts
├── refined/                     # distilled findings, one topic per file
│   ├── <finding-1>.md
│   └── <finding-2>.md
└── findings.md                  # summary + open questions + ingest candidates
```

`<topic>` is kebab-case, topic-named (not dated). Example: `.claude/research/xhs-customer-webhook/`.

## Core rules

1. **Raw stays raw** — `raw/` is a verbatim cache. Never edit for style or summary. If a file needs distillation, create a new file in `refined/`.
2. **Refined notes are atomic** — one finding per file, ≤ 80 lines. Longer = split.
3. **No decisions** — research describes options, constraints, precedent. Choosing among them is spec's job. Phrases like "we should use X" do not belong here; use "X is available, Y is available, tradeoffs: ..." instead.
4. **Open questions are first-class** — every research must end with an explicit list of unresolved questions. Empty list is a signal the research was too shallow.
5. **No auto-advance** — after `findings.md`, stop. Let the user decide next steps.
6. **Wikilinks are optional hints** — research notes MAY reference `[[wiki-page]]` but must not depend on wiki existing. If the wiki doesn't have a matching page, leave a plain name.
7. **Ingest is user-triggered** — the `findings.md` only *proposes* which items to ingest. Ingest itself runs through the `wiki` skill, invoked explicitly.
8. **Fetch is a strategy ladder, not a single call** — when Collect touches external URLs, follow [references/data-collection.md](references/data-collection.md). Silent dropping of a URL (e.g. "curl failed, moving on") is forbidden. Tabs / pagination / one-level referenced docs / primary assets must be covered per that reference. Unretrievable sources must be explicitly recorded as `raw/ext-<name>-failed.md` and surfaced in `findings.md`'s open questions.

## Initialization

If `.claude/research/` does not exist, create it silently on first use.

For each new research, create `.claude/research/<topic>/` and emit:

```
📁 .claude/research/<topic>/ 已创建
   下一步: 定义 question.md (scope + out-of-scope)
```

## What this skill does NOT do

- Does not pick a design / choose among alternatives (use `spec` skill)
- Does not produce tasks or code (use `task` / `impl` skills)
- Does not auto-ingest findings into the wiki (user-triggered via `wiki` skill)
- Does not gate on prior phases — `research` can be invoked cold

## When NOT to activate

- User already has a clear spec and asks for tasks → use `task` skill
- User asks a single point question answerable without exploration → just answer
- User is mid-impl and asks for a code-level explanation → explain in-line, do not open a research folder
- Research folder already exists with up-to-date `findings.md` → read it, do not re-collect

## Anti-patterns (do not do these)

See [references/anti-patterns.md](references/anti-patterns.md) for details. Quick list:

- Writing `findings.md` before `raw/` and `refined/` exist
- Collecting material outside the declared scope
- Embedding a design decision inside a refined note
- Auto-triggering spec skill at the end
- Producing a single 500-line `research.md` (must be split across `raw/` + `refined/`)
