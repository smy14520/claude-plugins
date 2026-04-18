# Maintenance Rules R1–R4

Four rules that keep the wiki from rotting. All are either automatic (R1, R4) or user-suggested (R2, R3).

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

## Interaction between rules

- **R1 and R4 are complementary**: R1 ensures new pages get linked from roots, which prevents them from becoming orphans. If R1 fails (no matching root found), R4 catches the page as orphan.
- **R2 and R4 are tightly coupled**: R4 updates index.md's orphan section, which R2 explicitly permits (the only case index.md lists non-root/non-cross-domain pages).
- **R3 is independent**: it's a user prompt that can happen alongside any operation.

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
