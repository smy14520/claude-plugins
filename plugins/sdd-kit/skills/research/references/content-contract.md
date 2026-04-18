# Research file content contracts

Each file in a research folder has a distinct purpose. Mixing them is the main failure mode.

## File-by-file contract

| File | Contains | Does NOT contain |
|------|---------|------------------|
| `question.md` | scope / out-of-scope / feeding decision | findings, raw excerpts, decisions |
| `raw/*.md` | verbatim excerpts with source refs | interpretation, abstraction, decisions |
| `refined/*.md` | one atomic finding per file | multiple findings, decisions, tasks |
| `findings.md` | summary + open questions + ingest candidates | full finding detail (link to refined/) |

## question.md contract

Purpose: freeze the scope so the research stays bounded.

Required sections:

- `# Question` — one sentence
- `## In scope` — 2-4 concrete sub-questions
- `## Out of scope` — ≥ 2 explicit exclusions
- `## Feeding decision` — what spec/task will consume this research
- `## Time budget` (optional) — rough hour/day estimate

Forbidden:

- Findings (nothing discovered yet)
- Tentative opinions ("I think we should...")
- References to wiki pages (question is pre-research)

## raw/ contract

Each file is a source-bounded excerpt cache.

Required sections:

- `# <Title>`
- `> Source: <URL | path | user>` blockquote
- `> Collected: YYYY-MM-DD`
- `## Content` — verbatim or near-verbatim excerpt

Forbidden:

- Interpretation ("this means X") — belongs in `refined/`
- Decisions ("so we should do Y") — belongs in spec
- Rewriting for style — raw is raw

### Allowed transformations on raw

- Truncation (cut irrelevant sections, note what was cut)
- Translation (if source is in another language) with note "Translated from <lang>"
- Format normalization (HTML → markdown)

### Not allowed

- Summarization that loses fidelity
- Merging multiple sources into one raw file (one source per file)
- Stripping citations or line numbers

## refined/ contract

Each file is **one atomic finding**. If you cannot name the file with a single specific topic, you are mixing findings — split.

Required sections:

- `# <Finding title>`
- `## What I found` — 1-3 sentences
- `## Where` — citations back to `raw/` files with line refs
- `## Why it matters` — connection to the feeding decision
- `## Open question` — what is still unknown (can be explicit "none")

Forbidden:

- Multiple distinct findings in one file
- Uncited claims ("I noticed" without a `raw/` ref)
- Decisions or recommendations

### Hard limits

- ≤ 80 lines per note
- One `raw/` citation minimum; if you cannot cite, the finding is speculative — move to `open question` or drop

### Optional frontmatter

```yaml
---
finding-type: landscape | gotcha | constraint | precedent
confidence: low | medium | high
---
```

## findings.md contract

Purpose: the one-file summary a spec author reads to know what this research produced.

Required sections:

- `# Research: <topic>`
- Frontmatter with `status: open | closed`, `date`
- `## Question` — copy from question.md
- `## Key findings` — ≤ 7 bullets, each a wikilink-style ref to a refined note
- `## Open questions` — bullets, for spec to resolve
- `## Ingest candidates` — refined notes worth promoting to wiki, each tagged with proposed type
- `## Ephemeral` — refined notes explicitly NOT for wiki (scoped to this decision)

Forbidden:

- Full detail of findings (link to refined/ instead; findings.md is a menu, not the content)
- Decisions ("we chose X") — decisions live in spec
- Auto-wiki-ingest side-effects (findings.md only *proposes*)

### The "read alone" test

`findings.md` should be readable by a spec author who hasn't read `raw/` or `refined/`. If they need to read the detail files to understand the summary, the summary is under-written.

## What happens to research after spec is written?

Research folders are **not deleted** after spec is finalized. They stay as historical record.

Optional: mark `findings.md` frontmatter `status: consumed-by-spec: <spec-name>` so future sessions know this research has landed.

## What about shared findings across multiple researches?

If finding X in research-A also applies to research-B:

- Link the refined note from both researches' `findings.md`
- If finding X is truly reusable, it is an **ingest candidate** — promote to wiki, then both researches can link to `[[wiki-page]]` instead of the original refined note
