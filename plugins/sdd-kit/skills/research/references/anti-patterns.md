# Research anti-patterns

Patterns seen in prior iterations (including `autolearn-sdd-kit`) that erode research quality. Avoid them.

---

## 1. The unbounded browse

**Symptom**: research folder grows to 20+ files over days, scope keeps expanding, findings.md never written.

**Why it happens**: no `question.md` upfront, or scope declared but `out-of-scope` list was empty.

**Correct approach**: always write `question.md` first with ≥ 2 explicit `out-of-scope` items. When something out-of-scope comes up, record it as an open question for a *future* research, do not expand the current one.

---

## 2. The single monolith

**Symptom**: one 500-line `research.md` in the root folder, no `raw/` or `refined/` subfolders.

**Why it happens**: convenience in the moment, no discipline around the 3-layer structure.

**Cost**: future sessions cannot find what they need; the file is unreadable as a whole; no clear "which parts are verbatim, which are interpretation".

**Correct approach**: enforce `raw/*.md` for sources and `refined/*.md` for distillations from day 1. Even a trivial research has at least one of each.

---

## 3. Decision smuggled into refined/

**Symptom**: a refined note says "we should use X" or "the right approach is Y".

**Why it happens**: the LLM feels confident while refining and wants to commit.

**Cost**: when spec runs later, the decision is already implicit, and alternatives aren't fairly weighed.

**Correct approach**: phrase as option-description. "X is available, Y is available. Tradeoffs: ..." Decisions happen in spec.

---

## 4. Auto-advancing to spec

**Symptom**: at the end of `findings.md`, the research skill opens a spec file and starts filling it.

**Why it is wrong**: violates the "阶段独立" principle. User may want to:

- Pause (think, gather external feedback)
- Do additional research
- Skip spec entirely (for a small prototype)
- Consume findings by other means

**Correct approach**: research ends at `findings.md`. Closing summary *suggests* next steps but does not act on them.

---

## 5. Uncited findings

**Symptom**: `refined/xxx.md` says "the API uses X pattern" without linking to the `raw/` source.

**Cost**: cannot verify; becomes received wisdom; may be false.

**Correct approach**: every refined note has at least one `raw/` citation. If you cannot cite, it is speculation — put it in "Open questions" or drop.

---

## 6. Research writing CLAUDE.md-style rules

**Symptom**: refined note ends with "always use X. never use Y. must do Z."

**Why it is wrong**: research records what exists, not what the project should enforce. Rules live in `CLAUDE.md` or equivalent.

**Correct approach**: describe observations; leave rule-making to spec or explicit style-guide authoring.

---

## 7. Ingest-during-research

**Symptom**: during refining, the skill writes to `.claude/wiki/` directly.

**Why it is wrong**: Wiki ingest is user-triggered. research may surface lots of findings that never matter; auto-ingest creates noise.

**Correct approach**: `findings.md` lists ingest *candidates*; actual ingest is a separate user action via `wiki` skill.

---

## 8. Treating user-pasted docs as refined material

**Symptom**: user pastes an article, the skill puts it directly into `refined/` with a new title, claiming it as distilled finding.

**Why it is wrong**: user-pasted material is raw. The value-add of research is distilling raw → refined.

**Correct approach**: user paste → `raw/user-input-YYYY-MM-DD.md`. Distillation happens in the refine step.

---

## 9. Parallel findings that should be one

**Symptom**: `refined/xhs-signature.md` and `refined/xhs-auth.md` both describe overlapping subsets of signature + auth behavior.

**Cost**: summary in findings.md becomes confusing; future reader has to cross-read.

**Correct approach**: if two refined notes overlap more than ~30%, merge. Refined notes should be disjoint concerns.

---

## 10. Findings.md without open questions

**Symptom**: "Open questions" section is empty or says "none".

**Why it is suspicious**: real exploration nearly always surfaces uncertainty. Empty open-questions usually means the research was surface-level.

**Correct approach**: before closing, actively challenge: "what would change my conclusion?" If nothing, state that explicitly: "No open questions — confirmed by trying to falsify each finding."

---

## 11. Overusing wikilinks

**Symptom**: every noun in a refined note becomes `[[wikilink]]`, including ones with no corresponding wiki page.

**Cost**: broken links; future lint noise; reader friction.

**Correct approach**: use `[[wikilink]]` only when a wiki page actually exists OR you are confident one will be ingested. Otherwise use plain names. Research notes are allowed to read without wiki.

---

## 12. Reusing a research folder across unrelated topics

**Symptom**: `.claude/research/general-research/` accumulates findings on multiple disjoint topics over months.

**Cost**: impossible to scope; `findings.md` becomes unusable.

**Correct approach**: one research folder per bounded question. If a new question arises, open a new folder, even if adjacent. Folders are cheap; attention isn't.

---

## 13. Fetch-and-give-up

**Symptom**: the skill tries `curl` (or its equivalent) against a URL, receives an error or empty body, and either silently omits the source or writes "couldn't fetch" into refined notes.

**Variants**:

- "403 / Cloudflare challenge, skipping this URL"
- "SPA, probably hard to scrape, moving on"
- "Used the search result snippet as the content"
- Fetching page 1 only on a paginated list
- Fetching one tab on a multi-tab page

**Cost**:

- Data incompleteness silently propagates to spec and downstream phases
- Spec decisions made on partial evidence
- Later reviewers cannot distinguish "this data is unavailable" from "we didn't try"

**Correct approach**: follow the strategy ladder and completeness rules in [data-collection.md](data-collection.md). Specifically:

- Exhaust the fallback chain (primary tool → fallback tool → next fallback) before declaring unretrievable
- Cover tabs, pagination (up to `max_pages`, default 10), and one-level material references
- Record failures as `raw/ext-<name>-failed.md` and surface them in `findings.md`'s open questions — never silent omission
- Never substitute a search-result snippet for the actual page content
- Never fabricate content inferred from URL or title
