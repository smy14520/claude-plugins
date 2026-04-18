# Maintenance Rules R1–R5

Five rules that keep the wiki from rotting. R1 and R4 are automatic; R2, R3, R5 are advisory (user decides).

---

## R1 — Root pages auto-update on ingest

**Trigger**: every time a new page is ingested.

**Action**:

1. Read the new page's `tags:` frontmatter
2. Find root pages whose tags overlap with the new page's tags
3. For each matching root:
   - Insert a wikilink in the most appropriate section of the root page
   - Add a one-line entry to the root's `版本演进` section if the change is significant

**Section mapping rule** (new page type → root section):

| New page type | Root section to update |
|------|------|
| `entity` (with `root` tag overlap) | 核心模块 or 已接入渠道 (whichever fits domain) |
| `entity` (basic module) | 基础设施 |
| `concept` | 设计模式 |
| `decision` | 关键决策 |
| `gotcha` | 已知陷阱 |
| `source` | 外部资料 |

**When a section does not apply to the root** (e.g. a root page has no 已接入渠道 section because it's not a multi-channel system): either add the section, or pick the closest existing section. Do not silently skip.

**Rule on "significance"**:

Update 版本演进 when:
- A new channel / provider / backend is added (user-facing)
- A major decision changes the architecture
- Not for every routine gotcha / minor concept

### Example

Ingest: `xhs-api.md` with `tags: [xhs, api, external, customer-service]`.

Matching root: `ai-customer-service.md` (has tag `customer-service`).

Action:
1. Insert `- [[xhs-api]]` under `## 已接入渠道` section of `ai-customer-service.md`
2. Append to 版本演进: `- YYYY-MM: 接入小红书（[[spec-xhs-customer-channel]]）`

---

## R2 — index.md exclusion list

**Trigger**: every time `index.md` is modified.

**Rule**: `index.md` must NOT contain references to:

- Child pages of any root (e.g. `xhs-api` — lives in `ai-customer-service.md`)
- Non-cross-domain concepts / decisions (live in their root's sections)
- Non-cross-domain gotchas (live in their root's 已知陷阱)

**index.md may ONLY contain references to**:

- Pages with `tags: [root]`
- Pages with `tags: [cross-domain]`
- Pages named `source-*.md` (source summaries)
- Orphan pages (by lint automation, see R4)

**Enforcement**: lint warns when index.md contains a page reference that violates R2. Such a page should either be:
- Removed from index.md (because it already belongs to a root), or
- Tagged `cross-domain` if it genuinely is cross-system, or
- Upgraded to `root` if it should be a domain hub

---

## R3 — Root promotion suggestion

**Trigger**: during ingest or lint.

**Detection**: a non-root page `P` that is referenced by ≥ 5 other pages.

**Action**: do NOT auto-promote. Instead, emit a suggestion:

```
💡 R3 suggestion: [[P]] is referenced by N pages. Consider promoting it to a root page.
Promotion procedure:
  1. Add `root` to P's frontmatter tags
  2. Restructure P's content to match the root page template
     (see references/index-and-root.md#root-page-template)
  3. Add P to index.md's 🏠 根实体 section
```

**Rationale**: automatic promotion risks restructuring a page that the user doesn't want restructured. Keep this decision with the user.

**Demotion** (reverse R3): not implemented. If a page was promoted to root but no longer warrants it (rare), the user removes the `root` tag manually and updates index.md.

---

## R4 — Orphan detection and index sync

**Trigger**: every lint run, and every ingest (cheaper version: only check the newly ingested page).

**Detection**:

- A page `P` is an orphan if:
  - `P` is not a root (does not have `tags: [root]`)
  - `P` is not `source-*.md`
  - No other page in `.claude/wiki/` contains `[[P]]`

**Action**:

1. Maintain the ⚠️ 孤立页面 section in `index.md`:
   - Add `P` to the orphan list if newly orphaned
   - Remove `P` from the orphan list if it got linked
2. Do not touch other sections of `index.md`

**Rationale**: orphans signal wiki health. Zero orphans = tight organization. Many orphans = needs cleanup.

**Threshold alert** (lint only):

```
If orphan_count / total_non_root_pages > 0.3:
  emit strong warning: "Wiki 组织可能失控，考虑整理或升级 root"
```

---

## R5 — Freshness signaling (stale-by-age)

**Trigger**: during `Query` (inline, per-page) and during `Lint` (batch report).

**Rationale**: GitHub Copilot's 2026-01 engineering post on memory quality states:

> "Memory quality is mostly a freshness and invalidation problem — **stale, branch-specific memories are often more dangerous than having no memory at all**."

A page that says "we decided X in Q2 last year" is actionable **only if the reader knows its age**. Hidden age = silent corruption risk.

**Decision: surface age, do not auto-invalidate.**

- We do NOT tie wiki pages to source-code mtimes (false-positive risk, maintenance burden).
- We do NOT auto-delete or auto-demote old pages (user judgment required).
- We DO surface per-page age as a neutral signal, and flag > 180 days as "review candidate".

**Thresholds** (applied against the page's last-modified time, or `date:` frontmatter if present):

| Age bucket | Query output | Lint classification |
|-----------|-------------|---------------------|
| < 90 days | no annotation | not flagged |
| 90–180 days | subtle hint (optional, e.g. `(3 months ago)`) | not flagged |
| 180–365 days | `(X months ago ⚠️)` | ⚠️ review candidate |
| > 365 days | `(X months ago ⚠️ stale)` | ⚠️ review candidate (strong) |

**Action** (Lint only, during the batch report):

```
⚠️ Review candidates (age-based, not broken — review and decide):
- [[decision-hmac-algo]]   8 months ago
- [[entity-old-crm]]       1 year ago (strong)
```

The user decides case-by-case whether to:
1. Leave untouched (still valid, just old)
2. Re-verify the claim and update `date:` frontmatter (refresh)
3. Mark as superseded with `deprecated: true` frontmatter (soft-delete)
4. Delete (hard)

**Excluded from R5**:
- `source-*.md` pages (external docs are intrinsically timestamped, no point flagging)
- Pages with `tags: [evergreen]` (explicit opt-out, for stable patterns that don't age)

**Forbidden**:
- Silently dropping aged pages from Query output (user must see them to decide)
- Auto-updating `date:` frontmatter without re-reading the page (defeats the whole signal)
- Using R5 flags as blocking errors (they are signals, not failures)

### Example: Query output with R5

```
📚 Wiki Query: "xhs webhook 签名"

### 已读取
- [[xhs-api]]                          (2 weeks ago)
- [[xhs-signature-clock-skew]]         (3 months ago)
- [[decision-hmac-algo]]               (8 months ago ⚠️)
- [[idempotent-webhook]]               (1 year ago ⚠️ stale)
```

### Example: Lint output with R5

```
❌ Real issues:
  - [[foo]] broken link to [[missing-page]]
  - [[bar]] orphan (no incoming links)

⚠️ Review candidates (age-based):
  - [[decision-hmac-algo]]   8 months ago
  - [[idempotent-webhook]]   1 year ago (strong)
```

Severity is visually distinct: ❌ = "broken, fix it"; ⚠️ = "check if still accurate".

---

## Interaction between rules

- **R1 and R4 are complementary**: R1 ensures new pages get linked from roots, which prevents them from becoming orphans. If R1 fails (no matching root found), R4 catches the page as orphan.
- **R2 and R4 are tightly coupled**: R4 updates index.md's orphan section, which R2 explicitly permits (the only case index.md lists non-root/non-cross-domain pages).
- **R3 is independent**: it's a user prompt that can happen alongside any operation.
- **R5 is orthogonal to R1-R4**: freshness is separate from linkage. A well-linked page can still be stale; an orphan can still be fresh. Lint reports them in separate sections.

---

## Failure modes and recovery

### R1 failure: ingested page does not match any root

Page becomes an orphan automatically (R4 catches it). No error. Next ingest or lint reveals orphan status and user can:
- Create a matching root
- Add `cross-domain` tag to the page (if appropriate)
- Leave as orphan temporarily

### R2 violation: someone added a child page to index.md

Lint detects and warns. User manually removes from index.md. No automatic fix because the remove may be intentional (e.g. if the child was promoted to `cross-domain`).

### R1 double-update: re-ingesting the same page

Before inserting the wikilink in the root, check if the wikilink already exists. If yes, skip the insertion but still update the 版本演进 if there's a semantic change.

---

## Tests (for future TDD)

When implementing automation around these rules, the following behaviors should have regression tests:

1. **R1 basic**: ingest `xhs-api.md` with tag `customer-service` → `ai-customer-service.md` gets `[[xhs-api]]` in 已接入渠道
2. **R1 no-root**: ingest `foo.md` with tag that no root has → page is orphan, index.md orphan section updated
3. **R1 multi-root**: ingest with tags matching 2 roots → prompt user (or pick max overlap)
4. **R2 violation**: manually add `[[xhs-api]]` to index.md → lint flags
5. **R3 suggest**: create 5 pages all linking to `[[foo]]` → lint suggests promoting `foo`
6. **R4 orphan cycle**: create orphan → link from another page → orphan section cleared
7. **R5 query age**: Query touches a page > 180 days old → output contains `⚠️` age annotation
8. **R5 lint candidates**: Lint on wiki with mix of fresh/stale pages → stale pages in `Review candidates` section, NOT in `Real issues` section
9. **R5 evergreen opt-out**: a page with `tags: [evergreen]` aged > 1 year → NOT flagged by Lint
10. **R5 source exclusion**: `source-*.md` aged > 1 year → NOT flagged
