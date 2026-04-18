# Operations: Ingest / Query / Lint

Detailed procedures for the three primitives. SKILL.md gives high-level steps; this file gives the full workflow including edge cases.

---

## Ingest

Distill new knowledge into a wiki page. Always user-triggered, never automatic.

### Trigger phrases (user intent)

- "记一下这个坑" / "记录这个经验"
- "沉淀一下 xxx" / "把 xxx 加到 wiki"
- "这个决定值得记下来"
- "让 wiki 收录这个"

### Full procedure

**Step 1 — Classify type**

Use the decision tree in [page-types.md#type-decision-tree](page-types.md):

1. External raw material? → `source`
2. Specific scenario + error + fix? → `gotcha`
3. Rationale for choosing among alternatives? → `decision`
4. Strips of proper nouns and still makes sense? → `concept`
5. Real object in this project? → `entity`

If ambiguous, **prefer the more specific type** (gotcha > decision > entity > concept).

**Step 2 — Determine file name**

Extract topic from user's description. Convert to **kebab-case, all lowercase**.

- Gotchas: name the scenario, not the topic. `xhs-signature-clock-skew` ✅, `xhs-api-issue` ❌
- Decisions: name the choice. `webhook-vs-poll-for-xhs` ✅, `xhs-integration` ❌
- Entities: name the entity. `xhs-api`, `user-service`
- Concepts: name the pattern. `idempotent-webhook`, `optimistic-lock`
- Sources: prefix `source-`. `source-xhs-api-doc`

**Step 3 — Check existence**

```bash
ls .claude/wiki/<filename>.md
```

If exists:

Prompt user: "页面 `<filename>.md` 已存在。要 (a) 合并到现有页面，(b) 创建新页面（改名），还是 (c) 取消？"

Wait for user choice before continuing.

**Step 4 — Apply template**

Load the template from [page-types.md](page-types.md) matching the type. Fill in from user's description.

**Important**: do NOT ask the user to fill every template section verbatim. Fill what you can infer from their description; leave sections they haven't covered as `_(待补充)_` placeholders with a note in the summary.

**Step 5 — Identify owning root page**

Scan the new page's `tags:` frontmatter. For each tag:

```bash
grep -l "tags:.*\b<tag>\b" .claude/wiki/*.md | xargs grep -l "tags:.*\broot\b"
```

Candidates are root pages whose tags overlap.

If exactly one match → that is the owning root.
If zero matches → page is an orphan (for now); do not auto-create a root, just note it.
If 2+ matches → prefer the root with the most tag overlap; if still ambiguous, ask user.

**Step 6 — Update owning root page (R1)**

See [maintenance-rules.md#r1](maintenance-rules.md) for the detailed rule. Short version:

- Insert wikilink in the matching section of the root page (已接入渠道 / 设计模式 / 已知陷阱 / etc.)
- Add one line to 版本演进 if the change is significant
- **Never rewrite existing root page content** — only append

**Step 7 — Append to log.md**

Single line format:

```
## [YYYY-MM-DD HH:MM] ingest | <type>: <name>
<optional one-line note>
```

**Step 8 — Output summary**

```
✅ Ingest 完成

- 新建页面: .claude/wiki/<name>.md (<type>)
- 归属 root: [[<root-name>]] (已更新)
- 待补充段落: <section-a>, <section-b>
- Log: 已追加
```

### Edge cases

**Case: user says "记一下" without enough detail**

Ask ONE targeted question to identify the type and key content. Never ingest a page with only the title and no body.

Good question: "这个坑的触发条件是什么？错误信息是什么？"
Bad question: "请填写以下所有字段..."

**Case: page already covers the topic but user wants to add new info**

Prefer **append to existing page** over creating a new one, unless the new info is a distinct gotcha / decision. Treat the existing page as living, not fixed.

**Case: the ingestion reveals a new root should exist**

If during ingest you realize several existing pages share a domain with no root, do NOT create a root unprompted. Finish the current ingest, then mention: "注意到 `<tag>` 领域已有 5+ 相关页面但无 root，建议考虑创建 root 页面 `<name>.md`。"

---

## Query

Retrieve knowledge for a specific task (e.g. spec drafting). Read-only.

### Trigger phrases

- "参考 wiki 里的 X"
- "查一下 wiki 有没有 X"
- "X 之前做过类似的吗"
- "wiki 里 X 是怎么设计的"

### Full procedure

**Step 1 — Read index.md**

```bash
cat .claude/wiki/index.md
```

Identify relevant entries across the five sections:

- 🏠 根实体 — system-level entry points matching the query
- 🧠 跨域通用模式 — abstract patterns matching the query
- 📋 跨系统决策 — cross-cutting decisions
- 📜 Source 摘要 — raw material references
- ⚠️ 孤立页面 — uncategorized pages (check last, may contain relevant matter)

**Step 2 — Read root pages**

For each relevant root page, read it fully. Note the grouped wikilinks under 核心模块 / 已接入渠道 / 关键决策 / 设计模式 / 已知陷阱 / etc.

**Step 3 — Selectively follow wikilinks**

Do NOT read every wikilink. Apply judgment:

- Reading 2-3 analogous child entities is usually useful (e.g. for `xhs` work, read `wechat-api` and `douyin-api` as analogs)
- Reading 1-2 key gotchas helps surface reproduction patterns
- Reading 1 key decision explains the "why" behind the architecture
- Skip wikilinks clearly irrelevant to the current query

**Step 4 — Also read cross-domain pages from index.md**

If the query involves an abstract pattern, read the cross-domain concept/decision even if it's already linked from a root.

**Step 5 — Output structured summary**

Annotate each `已读取` entry with a freshness hint per [R5-freshness](maintenance-rules.md#r5). Compute age from page's `date:` frontmatter if present, else filesystem mtime.

- `< 90 days`: no annotation
- `90–180 days`: `(X months ago)` — neutral
- `180–365 days`: `(X months ago ⚠️)` — yellow warning
- `> 365 days`: `(X months ago ⚠️ stale)` — strong warning
- `source-*.md` or `tags: [evergreen]`: never annotate

```
📚 Wiki Query: "<original query>"

### 已读取
- [[ai-customer-service]]                系统导航                    (2 weeks ago)
- [[wechat-api]]                          类比渠道                    (3 months ago)
- [[wechat-signature-clock-skew]]        签名类坑                    (8 months ago ⚠️)
- [[idempotent-webhook]]                  webhook 幂等模式             (1 year ago ⚠️ stale)

### 关键发现
- 点1（含引用）
- 点2（含引用）

### 未读取但可能相关
- [[douyin-concurrent-reply-risk]] — 如需并发控制再读
- [[source-wechat-customer-api-doc]] — 如需 API 细节

### 新鲜度提示
有 2 页标注 ⚠️（> 180 天未更新）。建议阅读时核对与当前代码/决策是否仍一致。
```

### Edge cases

**Case: user didn't specify scope, just "参考 wiki"**

Ask one clarifying question: "参考 wiki 里的哪方面？是架构决策、具体模块、踩过的坑，还是抽象模式？"

**Case: no relevant pages found**

Output: "Wiki 中未找到与 `<query>` 相关的页面。建议：在 research 阶段完成后再 ingest 相关发现。"

**Case: relevant pages exist but are stale**

Handled by R5-freshness inline annotation (see Step 5 above). No separate edge-case treatment needed — age hints are now part of every Query output.

---

## Lint

Audit wiki health. Read-only except for updating `index.md` orphans section.

### Trigger phrases

- "wiki 体检"
- "wiki 健康检查"
- "wiki lint"
- "清理一下 wiki"

### Full procedure

**Step 1 — Scan orphans**

Non-root pages that are not referenced by any other page:

```bash
# Pseudocode
for each page in wiki/ (excluding index.md, log.md, root pages):
    if no other page contains [[<page-name>]]:
        mark as orphan
```

**Step 2 — Scan broken wikilinks**

Wikilinks that target non-existent pages:

```bash
# Extract all [[xxx]] references and verify xxx.md exists
```

**Step 3 — Scan stale roots**

Root pages whose last-update time is older than the creation time of one of their children (indicates the child was added but the root wasn't updated — R1 violation):

```bash
for each root in wiki/ (tags contains root):
    root_mtime = stat(root).mtime
    for each child linked in root:
        if child_ctime > root_mtime and child not in root's wikilinks:
            flag as stale root
```

**Step 4 — Scan duplicate candidates**

Pages with filenames of high similarity (Levenshtein distance ≤ 3 among filenames > 10 chars):

```bash
# e.g. xhs-signature-clock-skew.md vs xhs-signature-timing-skew.md
```

These are manual-review signals, not automatic merges.

**Step 5 — Promotion candidates (R3)**

Pages referenced by 5+ other pages but missing `root` tag:

```bash
for each page:
    count = sum([1 for other in wiki/ if contains [[<page>]] in other])
    if count >= 5 and 'root' not in tags:
        suggest promotion
```

**Step 6 — Review candidates by age (R5)**

Scan all non-excluded pages for age > 180 days:

```bash
for each page in wiki/ (excluding source-*.md, pages tagged 'evergreen'):
    age = now - (page.date frontmatter || page mtime)
    if age > 180 days:
        classify as 'mild' (180-365) or 'strong' (> 365)
        add to review-candidates list
```

**These are signals, not errors.** They appear in a separate section of the report; they do NOT block commit or imply the page is wrong.

**Step 7 — Update orphans section**

Overwrite the ⚠️ 孤立页面 section of `index.md` with the fresh orphan list. Do not touch other sections.

**Step 8 — Append to log.md**

```
## [YYYY-MM-DD HH:MM] lint | orphans=N, broken=M, stale-roots=K, dup-candidates=L, review-candidates=R
```

**Step 9 — Output report**

Report is split into **two severity levels**:

- ❌ **Real issues** — something is structurally broken and must be fixed
- ⚠️ **Review candidates** — signals worth a look, but nothing is broken (user decides)

```
🧹 Wiki Lint Report

## ❌ Real issues (N + M + K + L)

### Orphans (N)
- [[xxx]] — created YYYY-MM-DD
- [[yyy]] — created YYYY-MM-DD

### Broken wikilinks (M)
- [[zzz]] referenced in [[aaa]] — no such page exists

### Stale roots (K)
- [[root-a]] — last updated YYYY-MM-DD, child [[bbb]] created later

### Duplicate candidates (L)
- [[xxx-foo]] vs [[xxx-bar]] — similar filenames, review manually

## ⚠️ Review candidates (R) — age-based, not broken

Per [R5-freshness](maintenance-rules.md#r5). These pages are old enough that their content may no longer reflect the current state of the code/decisions. Decide case-by-case:
1. Still valid → no action, or re-read and update `date:` to refresh
2. Outdated but kept for history → add `deprecated: true` frontmatter
3. Fully obsolete → delete

### Mild (180–365 days)
- [[decision-hmac-algo]]   8 months ago
- [[xhs-signature-clock-skew]]   6 months ago

### Strong (> 365 days)
- [[idempotent-webhook]]   1 year 4 months ago
- [[entity-old-crm]]   2 years ago

## 💡 Promotion candidates (R3)
- [[ccc]] — referenced by 7 pages, consider adding `root` tag

## Recommended next steps
- Fix real issues first (orphans / broken / stale-roots / duplicates)
- Then review candidates in descending age
```

### Edge cases

**Case: wiki is empty or near-empty (<5 pages)**

Skip lint with note: "Wiki 页面过少（<5），暂无需体检。"

**Case: too many orphans (>30% of total pages)**

Emit a strong warning:

```
⚠️ WARNING: 孤立页面占比 X%（> 30%），wiki 组织可能失控。
建议：(a) 集中做一次整理，把孤立页面归属到 root；(b) 考虑是否某些孤立页面本应是 root。
```
