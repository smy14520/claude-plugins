---
title: 单一 JSON 文件存储
description: Store 永久采用单一 JSON 文件 + 原子写入，永不引入数据库（人类硬约束）
type: decision
tags: [todo, storage]
---

# 单一 JSON 文件存储

个人本地 CLI、单用户、数据量小，Store 选定为单一 JSON 文件（`~/.todo-cli.json`），并以"写临时文件 + `os.replace` 原子重命名"落盘防止写坏。**这是人类在需求访谈中拍下的硬约束：永不引入任何数据库。**

## Considered Options

- SQLite — 否决：肉眼不可读、手改困难，读写能力远超单用户清单所需；
- 每目录 `.todo.json` — 否决：清单随目录分裂，与"全局一份 Store"的产品定位冲突。

## Consequences

- JSON 肉眼可读可手改，备份即复制文件；
- 无并发保护：多进程同时写会丢更新。单用户单终端场景可接受，不设锁。

## Revisit When

出现多机同步或多进程并发写需求时（届时优先追加锁或换存储，仍需重新过人类决策）。
