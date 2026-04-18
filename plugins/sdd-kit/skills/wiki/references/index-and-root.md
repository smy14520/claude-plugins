# index.md and Root Pages

The two-layer navigation design: `index.md` is the **meta layer** (site map), root pages are the **domain layer** (full inventory of each domain).

## index.md — what goes in, what doesn't

### Only FIVE sections allowed

```markdown
# Wiki Index

> 导航目录。进入某个领域的所有内容，请打开该领域的 root 页面。

## 🏠 根实体 · 领域入口

带 `tags: [root]` 的页面。每个 root 内部有该领域的完整子页面导航。

| 页面 | 说明 | 状态 |
|------|------|------|

## 🧠 跨域通用模式

带 `tags: [cross-domain]` 的 concept。不绑定具体系统，可复用。

| 页面 | 说明 |
|------|------|

## 📋 跨系统决策

带 `tags: [cross-domain]` 的 decision。影响多个系统。

| 页面 | 日期 |
|------|------|

## 📜 Source 摘要

原始资料摘要（official docs / papers / blog posts）。

| 页面 | 说明 |
|------|------|

## ⚠️ 孤立页面

未被任何页面引用的非 root 页面（由 lint 自动维护）。

| 页面 | 创建日期 |
|------|---------|
```

### What NEVER goes in index.md

- Any child page of a root (e.g. if `ai-customer-service` is a root, do NOT list `xhs-api` or `wechat-api` in index.md — they live inside the root page)
- Non-cross-domain concepts/decisions (they live inside their root's "设计模式" / "关键决策" sections)
- gotcha pages (they live inside their root's "已知陷阱" section)

### Why this rule matters

**Single source of truth**: every page appears in exactly ONE navigation location.

- Root child pages → appear in that root only
- Cross-domain pages → appear in index.md only
- Orphans → appear in index.md only (until adopted by a root)

Double-listing causes rot: you update one, forget the other, they drift.

### Organization logic: by usage intent, not by type

Each section maps to a real user query:

| User query | Section to check |
|------|------|
| "我要做某个系统相关的需求" | 🏠 根实体 |
| "我要找某个可复用模式" | 🧠 跨域通用模式 |
| "我要找某个跨系统决策" | 📋 跨系统决策 |
| "这个外部资料是哪来的" | 📜 Source 摘要 |
| "wiki 最近加了啥但没归类" | ⚠️ 孤立页面 |

If a section has no concrete user query tied to it, the section is wrong.

---

## Root pages — domain hubs

### When to create a root page

Create a root page for a system / module / project-level concept when **at least one** holds:

- It has identifiable sub-entities (like a customer service system has API adapters, message router, session store)
- It has multiple related decisions / gotchas worth aggregating
- It would otherwise spawn many orphan pages

### When NOT to create a root page

Do not create a root page for:

- Cross-domain abstract patterns (those are `concept` + `cross-domain` tag, NOT root)
- A single-purpose utility (just make a normal entity page)
- A temporary exploration that may not outlive the current project

### Promotion rule (R3)

If a non-root page is referenced by 5+ other pages, lint will suggest promoting it to root. Promotion procedure:

1. Add `root` to `tags` frontmatter
2. Restructure content to match root template (see below)
3. Add entry to `index.md`'s 🏠 根实体 section

### Root page template

```markdown
---
type: entity
tags: [root, <domain>]
aliases: [<alt-name>, ...]
date: YYYY-MM-DD
---

# <System Name>

> **根实体**：<one-line description>
> Code entry: <path>
> Initiated: YYYY-MM-DD

## 系统概览

3-5 lines describing:
- What this system does (positive)
- What it does NOT do (boundary)
- Key integrations

## 核心模块

Primary internal components.

- [[xxx]] — one-line purpose
- [[yyy]] — one-line purpose

## 已接入渠道 / 已使用的 <子领域>

Domain-specific subsection, rename as fits (channels, providers, backends, etc.).

- [[xxx]]
- [[yyy]]

## 基础设施

Infrastructure entities this system depends on.

- [[message-queue]]
- [[redis-session-store]]

## 关键决策

ADRs affecting this system.

- [[decision-xxx]]
- [[decision-yyy]]

## 设计模式

Concepts applied in this system (local use of reusable patterns).

- [[idempotent-webhook]]
- [[optimistic-lock]]

## 已知陷阱

Gotchas encountered during development/operation.

- [[xxx-signature-clock-skew]]
- [[yyy-race-condition]]

## 外部资料

Source summary pages relevant to this system.

- [[source-xxx-api-doc]]

## 版本演进

Brief timeline of major changes.

- YYYY-MM: 初版，仅支持 X
- YYYY-MM: 接入 Y
- YYYY-MM: 规划 Z ([[spec-z]])
```

### Rules for root page content

1. **Every bullet is a wikilink**. No prose descriptions of child entities — that info belongs on the child page itself.
2. **Sections are sorted by stability**: stable infrastructure first, volatile gotchas last.
3. **Leave empty sections in place** (with a placeholder note like `_(暂无)_`) so the structure is visible and easy to fill later.
4. **版本演进 section is append-only** — never rewrite history, only add.

### Rules for root page maintenance

When ingesting a new page whose tags overlap with a root page's domain:

1. Add a wikilink in the matching root section (核心模块 / 设计模式 / 已知陷阱 / etc.)
2. Update 版本演进 with a one-line note if the change is significant (new channel, major refactor, etc.)
3. Do NOT rewrite existing content — only append / add

See [maintenance-rules.md#r1](maintenance-rules.md) for the full automation rule.

---

## Example: browsing the wiki for "小红书客服" work

Walk-through with the complete design:

1. **LLM reads `index.md`** — sees `🏠 根实体` section; spots `[[ai-customer-service]]`
2. **LLM reads `ai-customer-service.md`** — sees grouped sections:
   - 已接入渠道: `[[wechat-api]]`, `[[douyin-api]]`
   - 关键决策: `[[webhook-vs-poll-for-customer]]`
   - 设计模式: `[[idempotent-webhook]]`
   - 已知陷阱: `[[wechat-signature-clock-skew]]`
3. **LLM selectively reads** 3-4 children it deems relevant (not all)
4. **LLM also reads** `index.md`'s 🧠 跨域通用模式 → `[[idempotent-webhook]]` (already linked)

Total reads: 1 (index) + 1 (root) + 3-4 (children) = 5-6 pages. Each read is purposeful.

Contrast with flat index.md: LLM would read 20+ page titles and still need to guess which are relevant to 小红书 work.
