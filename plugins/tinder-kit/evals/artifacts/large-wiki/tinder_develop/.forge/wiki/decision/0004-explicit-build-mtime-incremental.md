---
tags: [index]
---

# ADR-0004: 显式 build + mtime 增量，查询只读索引

## Status
Accepted（2026-09-25）

## Context
索引与 Vault 内容可能失步。可选：每次查询即席全扫（无索引价值）、查询前静默重建（不可预期）、或显式命令 + 增量。

## Decision
`build` 命令显式生成/更新索引：按 `(mtime, size)` 对比决定重扫哪些页，删除已消失页，派生结构（postings/backlinks/tags）全量重算（便宜）。查询命令**只读索引**；执行前轻量核对每个文件的 `(mtime, size)`，失步则向 stderr 警告"索引已过期，请先 build"，仍按现有索引尽力作答。

## Consequences
- 行为显式可预期，大库查询 O(索引) 而非 O(全库)；
- 增量重扫让日常 build 接近瞬时；
- 代价：忘 build 会看到过期结果 — 以 stderr 警告兜底，不做静默魔法。

## Amendment（2026-09-25，双轴审查修订）
原文「查询命令只读索引」精确化为：**查询的计算路径只读索引** — 求交、计分、排序绝不触碰 vault 文件（即使页面文件已被删除，检索仍可作答，有测试为证）。唯一例外属 **CLI 渲染路径**：`search` 的命中摘要（snippet）需要页面原文，由 CLI 层按需读取命中页文件；内核（`wikicore.model`/`Index`）保持零 vault IO。动机：索引不存原文副本以保「极简 JSON 索引」，而摘要渲染属展示逻辑，读单个命中文件的成本可忽略。原实现把该 IO 放进了内核（`Index.search(query, root)` 内部读文件），双轴审查发现后按本修订纠正。
