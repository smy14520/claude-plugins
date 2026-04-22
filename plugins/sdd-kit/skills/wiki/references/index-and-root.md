# index.md 与根页面

两层导航设计：`index.md` 是**元层**（站点地图），根页面是**领域层**（每个领域的完整清单）。

## index.md —— 什么该放，什么不该放

### 只允许五个段落

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

### 绝对不能出现在 index.md 中的内容

- 根页面的任何子页面（例如 `ai-customer-service` 是根页面，则 `xhs-api` 或 `wechat-api` 不得出现在 index.md 中——它们归属于根页面内部）
- 非跨域的概念/决策（它们归属于其根页面的"设计模式"/"关键决策"段落）
- gotcha 页面（它们归属于其根页面的"已知陷阱"段落）

### 为什么这条规则很重要

**唯一信息源**：每个页面只出现在一个导航位置。

- 根页面的子页面 → 只在该根页面中出现
- 跨域页面 → 只在 index.md 中出现
- 孤立页面 → 只在 index.md 中出现（直到被某个根页面收编）

重复罗列会导致腐化：更新了一个，忘了另一个，两者逐渐失同步。

### 组织逻辑：按使用意图，而非按类型

每个段落对应一个真实的用户查询：

| 用户查询 | 应查看的段落 |
|------|------|
| "我要做某个系统相关的需求" | 🏠 根实体 |
| "我要找某个可复用模式" | 🧠 跨域通用模式 |
| "我要找某个跨系统决策" | 📋 跨系统决策 |
| "这个外部资料是哪来的" | 📜 Source 摘要 |
| "wiki 最近加了啥但没归类" | ⚠️ 孤立页面 |

如果某个段落没有对应的真实用户查询，该段落就是多余的。

---

## 根页面 —— 领域枢纽

### 何时创建根页面

当满足以下**至少一项**时，为系统/模块/项目级概念创建根页面：

- 它有可识别的子实体（例如客服系统有 API 适配器、消息路由器、会话存储）
- 它有多个相关的决策/gotcha 值得聚合
- 否则会产生大量孤立页面

### 何时不创建根页面

以下情况不要创建根页面：

- 跨域抽象模式（它们是 `concept` + `cross-domain` 标签，不是 root）
- 单一用途的工具（直接创建普通 entity 页面即可）
- 可能不会比当前项目存活更久的临时探索

### 晋升规则（R3）

如果非根页面被 5+ 个其他页面引用，lint 会建议将其晋升为根页面。晋升步骤：

1. 在 frontmatter 的 `tags` 中添加 `root`
2. 重构内容以匹配根页面模板（见下文）
3. 在 `index.md` 的 🏠 根实体段落中添加条目

### 根页面模板

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
- YYYY-MM: 规划 Z ([[brainstorm-z]])
```

### 根页面内容规则

1. **每个条目必须是 wikilink**。不要为子实体写散文描述——那些信息属于子页面本身。
2. **段落按稳定性排序**：稳定的基础设施在前，易变的 gotcha 在后。
3. **保留空段落**（用 `_(暂无)_` 占位），使结构可见且便于后续补充。
4. **版本演进段落只允许追加**——绝不重写历史，只添加新条目。

### 根页面维护规则

当摄入的新页面其 tags 与某根页面的领域重叠时：

1. 在根页面的对应段落（核心模块 / 设计模式 / 已知陷阱 / 等）中添加 wikilink
2. 如果变更是重大变更（新渠道、重大重构等），在版本演进中追加一行说明
3. 不要重写已有内容——只追加/添加

完整自动化规则见 [maintenance-rules.md#r1](maintenance-rules.md)。

---

## 示例：浏览 wiki 查找"小红书客服"相关工作

完整设计的操作流程：

1. **LLM 读取 `index.md`** —— 看到 `🏠 根实体` 段落；发现 `[[ai-customer-service]]`
2. **LLM 读取 `ai-customer-service.md`** —— 看到分组的段落：
   - 已接入渠道: `[[wechat-api]]`, `[[douyin-api]]`
   - 关键决策: `[[webhook-vs-poll-for-customer]]`
   - 设计模式: `[[idempotent-webhook]]`
   - 已知陷阱: `[[wechat-signature-clock-skew]]`
3. **LLM 选择性读取** 3-4 个它认为相关的子页面（不是全部）
4. **LLM 还读取** `index.md` 的 🧠 跨域通用模式 → `[[idempotent-webhook]]`（已被链接）

总读取：1（index）+ 1（root）+ 3-4（子页面）= 5-6 页。每次读取都有明确目的。

对比扁平的 index.md：LLM 需要读取 20+ 个页面标题，仍需猜测哪些与小红书工作相关。
