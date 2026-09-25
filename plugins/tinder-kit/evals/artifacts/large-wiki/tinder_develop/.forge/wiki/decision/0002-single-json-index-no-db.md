---
tags: [index]
---

# ADR-0002: 单文件 JSON 索引，拒绝数据库

## Status
Accepted（2026-09-25）— 人类硬性约束，单向门级别

## Context
查询命令（backlinks/tags/search/doctor）需要跨页聚合数据。可选：SQLite、外部检索服务、或纯 JSON 文件。

## Decision
索引为 Vault 根下**唯一**的 `.wiki_index.json`（`version` + `pages` + `postings` 三段），`json` 标准库读写，先写 `.tmp` 再 `os.replace` 原子落盘。**严禁引入 SQLite 或任何外部检索服务**——这是本项目对"极简、零重型依赖"的硬性承诺。

## Consequences
- 索引随 Vault 目录整体拷贝/同步，无隐藏外部状态；
- 个人 wiki（数百页）规模下 JSON 读写延迟可忽略；
- 代价：超万页规模需重新评估 — 届时以新 ADR 推翻本条，而非绕过它。
