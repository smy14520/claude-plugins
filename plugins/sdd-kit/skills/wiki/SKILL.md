---
name: wiki
description: "Manage the project's persistent knowledge wiki at `.claude/wiki/` — structured pages with wikilinks, Karpathy LLM-Wiki pattern (NOT vector retrieval). Pages carry type=entity|concept|gotcha|decision|source in frontmatter; root pages (tag=root) serve as domain hubs. Three primitives: Ingest (record new knowledge), Query (read index → root → selective follow), Lint (orphans / broken links / stale roots). Invoke only on explicit user request (e.g. '用 wiki skill ingest / query / lint …')."
---

# Wiki — Persistent Knowledge Management

Manage `.claude/wiki/` as a structured knowledge graph across iterations. Users provide judgment and raw material; this skill handles the bookkeeping.

## Positioning

This skill is the **schema layer** of Karpathy's 3-layer LLM-Wiki:

- Raw sources → `.claude/research/`, code, external docs
- **Wiki (maintained here)** → `.claude/wiki/`
- **Schema (this SKILL.md + references/)** → tells the LLM how to maintain the wiki

**Core principle**: knowledge is a *compiled artifact*, not retrieved on-the-fly. The LLM is the librarian.

## Three primitives

Match user intent to one primitive. Full procedures in [references/operations.md](references/operations.md).

### 🟢 Ingest — distill new knowledge

Triggers: "记一下这个坑/经验/决定", "sink into wiki", "record this".

Procedure (detail in `references/operations.md#ingest`):

1. Classify type (entity | concept | gotcha | decision | source)
2. Determine file name (topic name, kebab-case, no type prefix)
3. Check if page exists → prompt merge-vs-new if yes
4. Apply template from [references/page-types.md](references/page-types.md)
5. Update owning root page per [references/maintenance-rules.md](references/maintenance-rules.md#r1)
6. Append one line to `log.md`
7. Emit summary

### 🔵 Query — recall existing knowledge

Triggers: "参考 wiki 里的 X", "wiki 里有没有 X", "have we done similar".

Procedure:

1. Read `.claude/wiki/index.md` → identify relevant root pages or cross-domain pages
2. Read the root page → scan its grouped wikilinks
3. Selectively follow wikilinks based on user's actual need (do not read everything)
4. Return a structured summary: pages read, key findings per page, related-but-unread leads

### 🟡 Lint — audit wiki health

Triggers: "wiki 体检", "wiki lint", "clean up wiki".

Procedure:

1. Scan orphans (non-root pages unreferenced by anything)
2. Scan broken wikilinks (links to nonexistent pages)
3. Scan stale roots (root page last update < some child page creation)
4. Scan duplicate candidates (filename Levenshtein distance < threshold)
5. Scan **review candidates by age** (pages older than 180 days, per [R5-freshness](references/maintenance-rules.md#r5))
6. Update `index.md`'s orphans section per [references/maintenance-rules.md](references/maintenance-rules.md#r4)
7. Output a markdown report with **two severity levels**: ⚠️ review candidates (signal, not error) vs ❌ real issues (broken / orphan / duplicate)

## Directory structure

```
.claude/wiki/
├── index.md          # navigation (root + cross-domain + source + orphans ONLY)
├── log.md            # append-only operation log
│
├── <root-topic>.md   # tag: [root] — domain hub (e.g. ai-customer-service.md)
├── <topic>.md        # subject-named page (e.g. xhs-api.md, idempotent-webhook.md)
│
└── source-<name>.md  # raw material summary (only prefix allowed)
```

## Core rules (quick reference)

Detailed rationale and procedures are in the `references/` files linked below.

1. **Naming** — file name = topic name in kebab-case. **No type prefix** except `source-`. See [references/page-types.md#naming](references/page-types.md).
2. **Type is frontmatter, not filename** — every page has `type:` in frontmatter (entity | concept | gotcha | decision | source).
3. **Root pages aggregate** — pages with `tags: [root]` serve as domain entry points. They list child wikilinks grouped by role. See [references/index-and-root.md](references/index-and-root.md).
4. **index.md is lean** — only lists root pages, cross-domain concepts/decisions, source summaries, and orphans. **Never list child pages of a root**. See [references/index-and-root.md#index-rules](references/index-and-root.md).
5. **entity pages are aggregation views, not code mirrors** — write info that requires reading 5+ files to reconstruct; do NOT write info that a single file or IDE index already provides. See [references/page-types.md#entity](references/page-types.md).
6. **Wikilinks policy**:
   - ✅ Wiki pages link freely to each other
   - ✅ Spec files MAY link to wiki pages (as background hints)
   - ❌ **Task files MUST NOT contain wikilinks** (execution plans must be self-sufficient)
   - ❌ Research notes rarely need wikilinks (ephemeral)

## Initialization

If `.claude/wiki/` does not exist, create it with seed files from [assets/templates/](assets/templates/):

```
.claude/wiki/index.md    ← from assets/templates/index.md
.claude/wiki/log.md      ← from assets/templates/log.md
```

After creation, append to `log.md`:

```
## [YYYY-MM-DD HH:MM] init | wiki initialized
```

## What this skill does NOT do

- Does not perform vector search or embedding-based retrieval (intentional — see Karpathy LLM-Wiki rationale)
- Does not auto-ingest (every ingest must be user-triggered)
- Does not store rules/style-guides/PSR-standards (those belong in `CLAUDE.md` or other skills)
- Does not create pages across the four types categorically named as `experience-*`, `module-*`, `rule-*` (anti-patterns — see [references/anti-patterns.md](references/anti-patterns.md))

## When NOT to activate

Do not run this skill when the user is:

- Asking a question that can be answered directly without wiki context
- Working on small local edits (bug fix, style change) unrelated to structured knowledge
- Explicitly opting out ("don't touch the wiki", "skip wiki")

When in doubt, run **Query** (read-only, cheap), not **Ingest**.
