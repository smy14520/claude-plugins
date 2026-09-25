---
title: 单一 .todos.json 本地存储，永不引入数据库
description: 拍板：数据只存 cwd 下单一 JSON 文件并直接覆写，明确排除 SQLite/PostgreSQL 等一切数据库与并发设计。
type: decision
tags: [task-management, storage]
---

# 单一 .todos.json 本地存储，永不引入数据库

todo CLI 是单机个人工具，数据量级为个人待办（数千条以内）。拍板：持久化只使用当前工作目录下的单一 JSON 文件（`.todos.json`），每次直接整体覆写；**永不引入 SQLite 或任何数据库**；单进程场景不考虑并发与原子写入。

## Considered Options

- SQLite：查询与并发能力强，但个人量级下是高射炮打蚊子，且数据无法直接 `cat`/git/手改救急——否决。
- todo.txt 纯文本：人读最友好，但 tags/priority/status 等结构化字段解析易脆——否决。

## Revisit When

- 出现多进程并发写需求（如多终端同时操作同一清单）；
- 单文件数据量或过滤性能成为实际痛点（> 数万条）。
