---
title: 索引仅用单文件 JSON 或纯内存，严禁数据库
description: wiki-cli 的索引与元数据只允许 .wiki_index.json 单文件或纯内存构建；不引入 SQLite/向量库/外部检索服务，工具对 vault 严格只读
type: decision
tags: [wiki, storage]
---

# 索引仅用单文件 JSON 或纯内存，严禁数据库

wiki-cli 的各子命令都依赖"解析 vault → 构建链接/标签索引"这一步。方案访谈中人类拍死硬边界：索引与元数据只允许两种形态——纯内存构建（v1 采用：每条命令全量重扫、无状态）或单文件 `.wiki_index.json` 缓存（未来性能需要时）；严禁引入 SQLite、向量库或任何外部检索服务。同时工具对 vault 严格只读，绝不提供任何写入笔记的路径。

## Considered Options

- SQLite（FTS5 可白拿全文检索）→ 否决：违背零依赖硬边界，引入二进制工件与 schema 迁移负担
- 向量库 / 外部检索服务 → 否决：网络与外部状态依赖，与"纯本地文件驱动"根本冲突

## Consequences

个人 vault（千级页面）全量重扫 < 1s，可接受；万级页面后单命令延迟线性增长。检索排序只能是启发式（标题命中 > 频次），无法升级为相关性算法——这是接受的上限。

## Revisit When

vault 超过约一万页面且单命令明显卡顿（> 2s）时，唯一允许的演进路径是引入 `.wiki_index.json` 单文件缓存，而不是数据库。
