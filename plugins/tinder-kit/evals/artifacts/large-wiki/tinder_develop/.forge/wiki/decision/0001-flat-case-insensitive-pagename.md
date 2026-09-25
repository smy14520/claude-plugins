---
tags: [wiki-syntax]
---

# ADR-0001: 扁平命名空间 + 大小写不敏感 PageName

## Status
Accepted（2026-09-25）

## Context
`[[page]]` 链接需要解析为某个 `.md` 文件。两种模型：路径敏感（`[[folder/page]]`，允许同名共存）与扁平命名空间（文件名即页面名，全库唯一）。

## Decision
采用**扁平命名空间**：PageName = 文件名去 `.md`，全 Vault 唯一，匹配大小写不敏感（casefold）。子目录仅是物理整理，不进入链接语义。build 时发现 casefold 冲突（重名页面）则报错且不落索引。

## Consequences
- 链接书写零路径负担，符合个人 wiki 主流习惯（Obsidian 式）；
- 大小写笔误不再产生假死链；
- 代价：无法存在同名页面 — 由 build 显式报错兜底，绝不稳定地静默任选其一。
