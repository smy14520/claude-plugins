# Page Types and Content Contracts

Five page types. Each has a distinct purpose and strict content contract.

## Naming convention (applies to all types)

- File name = topic name in **kebab-case**, all lowercase
- **No type prefix** (❌ `entity-xxx.md`, ❌ `gotcha-xxx.md`, ❌ `concept-xxx.md`)
- **Only `source-` prefix allowed** (for raw material summary pages)
- Type info lives in frontmatter `type:` field
- Topic names are domain-specific, not abstract (e.g. `xhs-api.md`, not `external-api.md`)

Examples:
- ✅ `ai-customer-service.md`, `xhs-api.md`, `idempotent-webhook.md`
- ✅ `xhs-signature-clock-skew.md`, `webhook-vs-poll-xhs.md`, `source-xhs-api-doc.md`
- ❌ `entity-xhs-api.md`, `gotcha-xhs-signature.md`, `decision-webhook.md`

## Frontmatter schema (all types)

```yaml
---
type: entity | concept | gotcha | decision | source
tags: [<domain>, <subdomain>, ...]
aliases: [<alt-name>, ...]     # optional, improves search
date: YYYY-MM-DD               # creation date (auto-set at ingest)
---
```

Special tags with semantic meaning:

- `root` — this page is a domain hub (aggregates child pages; listed in `index.md`)
- `cross-domain` — this page is reusable across systems/projects (listed in `index.md`)

---

## type: entity

**Definition**: a real, identifiable object with state, boundary, and version. APIs, service modules, database tables, external systems, queues, stores.

**Rule of thumb**: you should be able to answer "what *is* it?" rather than "how does it *work*?".

### Content contract

**Write these** (add value beyond code):

- Cross-file information aggregation (configs scattered across multiple files, callers scattered across modules)
- Constraints invisible in code (rate limits, signature rules, concurrency limits, correct usage patterns)
- Call topology and module boundaries
- Links to related decisions / concepts / gotchas

**Do NOT write these** (code already provides):

- API endpoint lists (official docs / OpenAPI spec handles this)
- Method signature lists (IDE handles this)
- Database column lists (schema file handles this)
- Configuration key lists (config file handles this)

### The 5-file test (hard rule)

For every piece of information on an entity page, ask: **"How many files does the AI need to read to reconstruct this info from code?"**

- 1 file to reconstruct → **do not write** (it's noise)
- 5+ files to reconstruct → **write** (it's real value)

### Template

```markdown
---
type: entity
tags: [<domain>, ...]
date: YYYY-MM-DD
---

# <Entity Name>

> Code entry: <path>
> Related: [[module-a]], [[module-b]]

## Responsibility boundary

Explicit 2-3 lines: what it does / what it does NOT do.

## Cross-file configuration

- Config A: in `path/to/file1.php` key `xxx`
- Config B: in `path/to/file2.yaml` key `yyy`
- Env vars: `FOO_*`

## Call topology

Who calls this entity:
- [[module-a]] — for purpose X
- [[module-b]] — for purpose Y

What this entity depends on:
- [[downstream-api]]
- [[redis-session-store]]

## Constraints (not visible in code)

- Rate limit: X req/min
- Concurrency: must serialize per-session
- Error handling: retry pattern, circuit breaker threshold

## Related

- Key decisions: [[decision-xxx]]
- Design patterns: [[concept-xxx]]
- Known issues: [[gotcha-xxx]]
```

---

## type: concept

**Definition**: an abstract thought / pattern / methodology that retains meaning when stripped of specific entity names. Reusable across projects.

**Rule of thumb**: strip out all proper nouns — does the page still make sense? If yes, it's a concept.

### Content contract

Required sections:

- **Applicable scenarios** — when should this pattern be used?
- **Core idea** — the essence, language-agnostic
- **Trade-offs** — advantages, costs, non-applicable cases
- **Application example(s)** — at least one `[[entity-xxx]]` link showing where it's used in this project

### Template

```markdown
---
type: concept
tags: [<domain>, ...]
date: YYYY-MM-DD
---

# <Concept Name>

## Applicable scenarios

When you have problem X with constraints Y.

## Core idea

The essence of the pattern, 2-4 sentences, abstract.

## Trade-offs

- Advantages: ...
- Costs: ...
- Does not apply when: ...

## Application example

- [[xxx]] uses this to handle ...
- [[yyy]] uses this with variation: ...

## References

- Origin / inspiration (book / paper / blog), if any
```

---

## type: gotcha

**Definition**: one specific scenario + one specific error + one specific workaround. Concrete, reproducible, short.

### Content contract

Required sections:

- **Reproduction** — how to trigger the problem (conditions, inputs)
- **Symptom** — what goes wrong (error message, wrong behavior)
- **Root cause** — why it happens
- **Workaround** — the verified fix

### Strict limits

- **Page length ≤ 50 lines**. If longer, you've mixed multiple gotchas — split.
- Title must describe a **specific scenario**, not a general topic.
  - ✅ `xhs-signature-clock-skew.md`
  - ❌ `xhs-api-issues.md`

### Template

```markdown
---
type: gotcha
tags: [<domain>, ...]
date: YYYY-MM-DD
severity: low | medium | high | critical
---

# <Specific scenario>

## Reproduction

1. Setup: ...
2. Action: ...
3. Observe: ...

## Symptom

```
<error message or behavior>
```

## Root cause

Technical explanation of why this happens.

## Workaround

The verified fix. Code or config snippet.

## Related

- [[entity-xxx]] — affected entity
- [[decision-xxx]] — if relevant
```

---

## type: decision

**Definition**: an Architecture Decision Record (ADR). Focus on **"why this and not that"**, not on "what was built".

### Content contract

Required sections:

- **Context** — what problem forced a decision
- **Alternatives** — at least 2 options considered
- **Decision** — what was chosen
- **Consequences** — positive and negative outcomes, trade-offs accepted

### Template

```markdown
---
type: decision
tags: [<domain>, ...]
date: YYYY-MM-DD
status: proposed | accepted | superseded | deprecated
---

# <Decision title: "Use X for Y">

## Context

What forced this decision? What constraints applied?

## Alternatives considered

### Option A: <name>
- How it works: ...
- Pros: ...
- Cons: ...
- **Rejected because**: ...

### Option B: <name>
- ...
- **Accepted because**: ...

### Option C: <name> (if any)
- ...

## Decision

Option B.

## Consequences

- ✅ Positive outcome
- ⚠️ Accepted trade-off
- 🔄 Future revisit trigger (what would make us reconsider)

## Related

- Implemented in: [[entity-xxx]]
- Design pattern: [[concept-xxx]]
- Replaces: [[decision-yyy]] (if applicable)
```

---

## type: source

**Definition**: a summary page for external raw material (official docs, papers, blog posts, specs).

**This is the only page type that gets a filename prefix**: `source-<name>.md`.

### Content contract

- Brief summary of what the source covers (2-4 paragraphs)
- Key takeaways applicable to this project
- Link to the original source
- Links to related entity/concept pages this source informed

### Template

```markdown
---
type: source
tags: [<domain>, <source-type>]
date: YYYY-MM-DD
origin: <URL or citation>
---

# <Source Title>

> Original: <URL>
> Accessed: YYYY-MM-DD

## Summary

2-4 paragraphs of what the source covers.

## Key takeaways for this project

- Point 1 that applies to us
- Point 2 that applies to us

## Informed pages

- [[entity-xxx]] — how this source shaped the entity
- [[concept-xxx]] — abstract pattern derived from this source
```

---

## Type decision tree (when ingesting)

When the user asks to ingest, classify with this tree:

1. Is it an **external raw material** (doc / paper / blog)? → `source`
2. Is it a **specific scenario + error + fix**? → `gotcha`
3. Is it a **rationale for choosing one approach over alternatives**? → `decision`
4. Can it be **stripped of proper nouns and still make sense**? → `concept`
5. Is it a **real object in this project** (API, module, table, queue)? → `entity`

If ambiguous, prefer the more specific type (gotcha > decision > entity > concept) so it carries more constraint signal.
