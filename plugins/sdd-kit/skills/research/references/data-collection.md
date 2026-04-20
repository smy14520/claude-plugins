# Data Collection Strategy

Detailed procedures for the Collect primitive's URL-fetching step. Applies whenever
`research.Collect` needs to retrieve a URL (or an externally-hosted artifact) and save
it under `raw/ext-<name>.md`.

> **Invoked from**: [`../SKILL.md`](../SKILL.md) (Collect primitive, step 3).
> **Also referenced from**: `wiki` skill's source-* ingest path (cross-skill reuse).

## Core principle

**Fetch is a strategy ladder, not a single call.** A single `curl` attempt that fails
and falls back to "I couldn't get this" is an anti-pattern. The ladder below must be
exhausted before declaring failure.

The ladder's goals, in order:

1. **Right tool for the URL type** (choose the cheapest tool that can actually succeed)
2. **Completeness over first-impression** (one URL rarely = one file)
3. **Explicit failure trail** (never silently drop a URL)

---

## 1. Tool dispatch matrix

Choose the primary tool by URL shape and content characteristics. Use the fallback
when the primary cannot extract usable content.

| URL / target shape | Primary | Fallback(s) | Why primary |
|---|---|---|---|
| GitHub repo — README, source file, wiki page | `deepwiki` | direct `raw.githubusercontent.com` fetch → `playwright` | Pre-indexed with semantic Q&A; far cheaper than scraping the rendered page |
| Library / SDK / framework API docs (React, Next.js, AI SDK, Tailwind, etc.) | `context7` | `playwright` | Purpose-built for framework doc retrieval; returns structured doc sections |
| Static HTML, RSS, known JSON API | built-in fetch (curl-equivalent) | `playwright` | Cheapest; do not over-engineer |
| JS-rendered / SPA / requires script execution | `playwright` | `js-reverse` (when an underlying API call can be reversed) | Needs a real browser runtime |
| Tab-switching / paginated list / infinite scroll | `playwright` (navigate each state) | — | Multi-step navigation unavoidable |
| Requires login / authenticated content | `playwright` + session reuse | — | Relies on browser identity; no alternative |
| Current news / recent events / real-time facts | `grok-search` | `exa` | `grok-search` includes recency signals |
| Unknown exact URL — only have topic | `exa` (neural / semantic) | `grok-search` | Locate first, then re-enter the matrix with the found URL |
| API reference for a specific symbol / function | `context7` | `deepwiki` (if in GitHub) | `context7` returns the relevant doc section directly |

**Notes on tool selection:**

- Always prefer a structured / indexed source (`deepwiki`, `context7`) over raw scraping
  when the URL's content is already covered by one.
- `js-reverse` is a specialist: use it only when `playwright` can reach the content but
  doing so is expensive (large page, many requests), AND there is a discoverable
  backend API call (network tab shows a clean JSON endpoint).
- `exa` and `grok-search` are discovery tools. Once they return a URL, re-enter this
  matrix with that URL — do not treat the search result snippet as final content.

---

## 2. Fallback ladder — mandatory, not optional

When the primary tool fails:

1. Do NOT give up. Invoke the next tool in the fallback column.
2. If all tools in the row fail, record the failure trail (see §5) and emit a
   `raw/ext-<name>-failed.md` entry. Do NOT silently omit the URL.
3. User-facing summary in `findings.md` must cite what was tried and why each failed.

**Anti-patterns** (explicit bans):

- "curl returned 403 so I skipped this source" — must escalate to `playwright`.
- "This is a SPA so probably hard, moving on" — must still try `playwright`.
- "The search result had a snippet, I used that as the content" — snippets are teasers,
  not sources. Fetch the actual URL.
- "Two of three tools in the fallback chain failed, I'll stop" — try the third.

---

## 3. Completeness rules

A single URL almost never maps to a single raw file. Before declaring a source
collected, verify the following dimensions:

### 3.1 Tab completeness

If the page has multiple tabs (e.g. "Overview | API | Examples | Discussion"), collect
each tab separately. File per tab:

```
raw/ext-<name>-overview.md
raw/ext-<name>-api.md
raw/ext-<name>-examples.md
raw/ext-<name>-discussion.md
```

If any tab's content is redundant with another (e.g. "Print view" duplicates
"Overview"), skip with a one-line note in frontmatter rather than silently dropping.

### 3.2 Pagination

For paginated lists (forums, API paged results, "load more" buttons):

- Default ceiling: **10 pages** (or first empty page / end-of-list signal, whichever
  comes first).
- Override per research: add `fetch.max_pages: N` to the topic's `question.md`
  frontmatter. Applies to all paginated URLs in that research.
- Stop conditions (any one triggers stop): empty page / identical content to previous
  page / `max_pages` hit / server returns 404/410 for next page.
- Per-page record: save each page as `raw/ext-<name>-p{N}.md`. Do not merge pages into
  one file — lose granularity, hard to re-audit.

### 3.3 One-level follow

If the primary page explicitly references ("see also", "related docs", "referenced
in") external documents that are material to the research question, follow **one
level** of these links. Do not recurse.

- Follow depth: 1.
- Save followed pages as `raw/ext-<name>-ref-<short>.md`.
- Do NOT auto-follow inline hyperlinks that are merely decorative (nav menus, author
  bios, footers).

### 3.4 Asset carry

If images, PDFs, or other binary assets carry primary information (diagrams in a
paper, screenshots in a tutorial), download them to:

```
raw/assets/<topic>/
```

Reference them from the corresponding `raw/ext-*.md` by relative path. Do not rely on
remote URLs — external assets can rot.

### 3.5 Metadata frontmatter

Every `raw/ext-*.md` file MUST start with:

```yaml
---
url: <original URL>
tool: <fetch tool used, e.g. playwright / deepwiki / context7>
fetched_at: YYYY-MM-DD HH:MM
strategy: <brief — e.g. "paginated, 7 pages collected, stopped on empty">
page_of_set: <e.g. "3/7" if part of pagination, omit otherwise>
---
```

This metadata makes later audits (spec DRIFT, review) able to trace every claim back
to a timestamped retrieval.

---

## 4. Override in question.md

Per-research overrides live in the topic's `question.md` frontmatter:

```yaml
---
status: open
date: YYYY-MM-DD
feeding: <spec-name>

# Optional fetch overrides:
fetch:
  max_pages: 50               # default 10
  follow_depth: 2             # default 1; rarely needed
  tools_force: [playwright]   # skip the matrix, always use this tool
  tools_exclude: [js-reverse] # never invoke this tool
---
```

Overrides apply only to the current research topic. No global defaults are changed.

---

## 5. Failure handling

When a URL cannot be retrieved after exhausting the fallback ladder:

### 5.1 Record, don't drop

Create `raw/ext-<name>-failed.md`:

```markdown
---
url: <URL>
attempts:
  - tool: deepwiki
    error: "not a GitHub URL"
    at: 2026-04-20 14:05
  - tool: playwright
    error: "timeout after 30s, Cloudflare challenge"
    at: 2026-04-20 14:07
  - tool: js-reverse
    error: "no backend API visible in network trace"
    at: 2026-04-20 14:12
final_status: unretrievable
---

# Why this matters

<1-2 lines on what this source was expected to contribute>

# What the research will proceed with instead

<what substitute sources or explicit "gap" acknowledgment>
```

### 5.2 Propagate to findings.md

In `findings.md`'s "Open questions" section, add:

```markdown
- ⚠️ Could not retrieve [<source name>](<URL>) — tried deepwiki, playwright, js-reverse.
  See `raw/ext-<name>-failed.md`. The spec must decide whether to proceed without this
  input or find an alternative source.
```

This ensures the spec phase cannot silently assume "research covered everything."

### 5.3 Never fabricate

If a source is unretrievable, **do not** infer its contents from the URL, title, or
search result snippets. Fabrication at the raw layer poisons every downstream phase.

---

## 6. Tool invocation notes

Tool invocations vary by runtime (MCP server, CLI, built-in tool). The following are
guidance, not strict syntax — adapt to the executing agent's available bindings.

### deepwiki

For GitHub repos. Typical invocation targets either the repo root or a specific file
path. Returns structured Q&A-ready content.

### context7

For library docs. Typical invocation: specify the library (e.g. `ai-sdk`, `react`,
`tailwindcss`) plus a topic. Returns curated doc snippets with version tags.

### playwright

For JS-rendered content. Typical use: navigate to URL, wait for selector, extract
content. For tabs: iterate through tab triggers. For pagination: click "next" until
stop condition.

### js-reverse

For deriving backend API from frontend behavior. Use only when playwright succeeds
but is expensive AND the site uses a clean JSON backend. Typical use: inspect network
trace, identify the API endpoint, re-fetch that endpoint directly.

### grok-search

For real-time / recent content. Typical use: query phrase + optional time window.

### exa

For semantic / neural search. Typical use: topic phrase, returns URLs ranked by
semantic relevance.

### Built-in fetch (curl-equivalent)

For static HTML / RSS / JSON. Respect robots.txt; include User-Agent header when the
target requires one; retry 2x on 5xx before escalating.

---

## 7. Boundary — when NOT to use this

This reference governs the **Collect** primitive only. Do not apply to:

- **Refine** — refined notes are human-style distillation, not re-fetches.
- **Findings** — findings reference already-collected raw material, no new fetches.
- **Spec** — spec must not fetch; if a spec needs data, it's a gap that sends control
  back to research.
- **Impl** — impl reads task's deliverable/acceptance, not external URLs. External
  fact-fetching at impl time = research-in-the-wrong-phase, bounces to NEEDS_CONTEXT.
- **Wiki ingest of non-source pages** — only `source-*` pages follow this. Entity /
  concept / gotcha / decision pages are distilled from existing research or code, not
  re-fetched.

---

## 8. Checklist — before declaring Collect complete

For each URL in the research's input set:

- [ ] Primary tool attempted
- [ ] If primary failed, at least one fallback attempted
- [ ] Tab completeness verified (or confirmed single-tab)
- [ ] Pagination ceiling reached (or confirmed non-paginated)
- [ ] One-level follow done (or confirmed no material references)
- [ ] Assets downloaded (or confirmed no primary assets)
- [ ] Each `raw/ext-*.md` has full frontmatter metadata
- [ ] Failed URLs recorded in `raw/ext-*-failed.md` and surfaced in `findings.md`

If any checkbox is unchecked, Collect is not done — either finish the step or document
why it was skipped.
