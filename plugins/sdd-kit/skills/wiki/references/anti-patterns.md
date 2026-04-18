# Anti-patterns

Things this skill must NOT do. Each is a concrete failure mode observed in prior designs (autolearn-sdd-kit, spf, etc.) or warned against in Karpathy's LLM-Wiki essay.

---

## ❌ AP1 — Vector retrieval / embedding-based search

**Do not** build or invoke any vector store, embedding model, or similarity-based retrieval over wiki content.

**Why**: Karpathy's LLM-Wiki rationale — the wiki IS the retrieval mechanism. Pages and wikilinks provide structured, explicit, low-noise access. Vectors add:

- Irrelevant-but-similar chunks (noise)
- Opaque "why did this get retrieved" (black box)
- Rebuild cost on every update (maintenance)

**Correct approach**: explicit navigation via `index.md` → root → children.

---

## ❌ AP2 — Auto-ingest without user trigger

**Do not** automatically ingest anything. Never silently create pages during research / spec / task / impl phases.

**Why**: the judgment of "what's worth sinking" is the user's main value-add. Auto-ingest:

- Fills the wiki with noise
- Trains the user to ignore wiki content
- Makes user lose track of what's in there

**Correct approach**: every ingest is triggered by an explicit user phrase. When in doubt, ask first.

**Exception**: R1 (auto-update root page on ingest) is fine because it's a side effect of a user-triggered ingest, not a standalone action.

---

## ❌ AP3 — Categorical type prefixes in filenames

**Do not** name files `entity-xxx.md`, `concept-xxx.md`, `gotcha-xxx.md`, `decision-xxx.md`.

**Only** `source-xxx.md` prefix is allowed.

**Why**: filename prefixes:

- Force type classification at naming time (often premature)
- Make filenames longer than they need to be
- Imply a "type" is the primary navigation axis (it's not — subject is)
- Break compatibility with Obsidian graph views

**Correct approach**: file name = topic name. Type goes in frontmatter.

See prior art: luotwo/llm-wiki does exactly this. spf does NOT and creates maintenance burden.

---

## ❌ AP4 — Experience / module / rule as page categories

**Do not** create pages of type `experience`, `module`, or `rule`.

**Why**:

- **"Experience"** is too broad — a grab-bag of gotchas, decisions, and random notes. Over time it becomes unnavigable.
- **"Module"** overlaps with `entity`. Every code module is an entity; separating them creates false dichotomy.
- **"Rule"** belongs in `CLAUDE.md` or a skill, not in wiki. Wiki describes what exists / what happened; rules prescribe what SHOULD be done.

**Correct mapping from legacy (autolearn-sdd-kit)**:

| Old | New |
|------|------|
| `experience/*.md` | Split into `gotcha-*` and `decision-*` pages |
| `modules/*.md` | Convert to `entity` pages with appropriate tags |
| `modules/INDEX.md` | Remove — replaced by root page for the system |
| `rules/*.md` | Move to `CLAUDE.md` or a dedicated skill |
| `gotchas/*.md` | Rename with specific scenario (not topic) — `xhs-signature-clock-skew` ✅ |

---

## ❌ AP5 — MOC (Maps of Content) layer files

**Do not** create standalone `moc-xxx.md` files to aggregate topics.

**Why**: MOC adds a meta-layer on top of real content. Maintenance cost:

- Every new page: decide which MOC it belongs to
- MOCs themselves accumulate — eventually needing a "MOC of MOCs"
- When topic boundaries shift, MOCs need rewriting

**Correct approach**: root entity pages (with `tags: [root]`) serve the same purpose. Aggregation is a natural byproduct of describing the domain entity, not a separate layer.

---

## ❌ AP6 — Mechanical code transcription in entity pages

**Do not** write entity pages that copy information a single code file already provides.

**Examples of what NOT to write**:

- The complete list of methods on `UserService` (IDE provides this)
- The complete list of API endpoints (OpenAPI spec provides this)
- The complete list of database columns (schema file provides this)
- The complete list of config keys (config file provides this)

**Why**: Such info:

- Goes stale as code evolves
- Adds no value over running `grep` or IDE lookup
- Confuses the reader about what the entity page is *for*

**Correct approach**: the 5-file test — write only info that requires reading 5+ files to reconstruct. See [page-types.md#entity](page-types.md).

---

## ❌ AP7 — Strong cross-document coupling

**Do not** write:

- In `tasks/*.md`: any `[[wikilink]]` — tasks must be self-sufficient execution plans
- In `research/*.md`: heavy cross-referencing — research is ephemeral, not canon
- In `wiki/*.md`: "REQUIRED: read X first before using Y" — wiki consumers choose what to follow

**Why**: strong coupling forces readers into predetermined paths. The user's design philosophy is user-in-control; wikilinks are HINTS, not mandates.

**Correct approach**:

| Document | Wikilink policy |
|------|------|
| `.claude/tasks/*.md` | ❌ Must NOT contain wikilinks |
| `.claude/research/*.md` | 🟡 Minimal, ephemeral |
| `.claude/specs/*.md` | 🟢 May link to wiki as background |
| `.claude/wiki/*.md` | ✅ Link freely between wiki pages |

---

## ❌ AP8 — Hidden auto-chaining between skills

**Do not** design the wiki skill to automatically invoke other skills (research / spec / task / impl). Likewise, do not let other skills silently invoke wiki operations.

**Why**: the user has explicitly chosen a non-pipeline, user-controlled workflow. Every phase transition is a user decision.

**Correct approach**:

- Wiki skill returns results. User decides next step.
- Other skills may *mention* wiki content as input (e.g. spec skill may say "please run wiki query if you want to pull prior art"), but NEVER silently invoke wiki operations.

---

## ❌ AP9 — Timestamp-free everything

**Do not** create pages without `date:` in frontmatter, and do not write to log.md without `[YYYY-MM-DD HH:MM]` prefix.

**Why**: `log.md` is a critical tool for session recovery (per Karpathy's original essay). Without timestamps:

- `grep "^## \[" log.md | tail -5` stops working
- Stale-root detection (R1.5) stops working
- "What did we do last week?" becomes unanswerable

**Correct approach**: every mutation — ingest, lint, init — includes timestamp.

---

## ❌ AP10 — Hiding schema changes

**Do not** modify the schema (this SKILL.md or `references/*.md`) silently. Any change to how pages are structured must be announced.

**Why**: page templates are contracts. Changing them invalidates existing pages.

**Correct approach**: if the schema evolves (e.g. adding a new required frontmatter field), either:

- Migrate all existing pages (preferred for small wikis), or
- Mark the new requirement as applying only to new pages and document the cutover in log.md

---

## Summary table

| # | Anti-pattern | Guard in skill |
|---|------|------|
| AP1 | Vector retrieval | Skill logic uses explicit navigation only |
| AP2 | Auto-ingest | Every ingest requires user trigger phrase |
| AP3 | Type-prefix filenames | Naming validator rejects `entity-`, `concept-`, `gotcha-`, `decision-` prefixes |
| AP4 | Experience/module/rule types | Type enum strictly limited to 5 values |
| AP5 | MOC layer | Root pages are regular entities with `root` tag, not separate files |
| AP6 | Mechanical transcription | 5-file test in entity contract (page-types.md) |
| AP7 | Strong coupling | Wikilink policy table enforced by convention |
| AP8 | Hidden skill chaining | Wiki skill is stateless — returns results, does not invoke other skills |
| AP9 | Missing timestamps | Frontmatter `date:` required; log.md format enforced |
| AP10 | Silent schema changes | Schema changes logged explicitly |
