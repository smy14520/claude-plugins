---
title: .todos.json 的仓库外消费者
type: cross_cut
tags: [storage, sync]
description: 手机端同步服务 todo-sync 与月度报表任务直接读取 .todos.json，改存储格式必须联动
anchors: [DB, load, save]
---

# .todos.json 的仓库外消费者

`.todos.json` 不只被 `todo.py` 读写。两个**不在本仓库**的程序直接读取它，代码里 grep 不到：

1. **todo-sync（手机端同步服务，另一个仓库）**：每 5 分钟读取 `.todos.json`，按 `id` 做增量同步。它假设：
   - 文件顶层是**数组**；
   - `id` 是**单调递增的整数**，用 `max(id)` 作为同步水位线。
2. **月度报表 cron 任务（运维机上的 `report_todos.sh`）**：用 `jq '.[] | select(.done)'` 统计完成数，同样假设顶层是数组。

## 改动联动清单

- 改顶层结构（比如包一层 `{version, tasks}`）→ todo-sync 与报表任务都会读空，必须先发 todo-sync 新版本并更新 `report_todos.sh`；
- 改 `id` 类型（比如换成 uuid）→ todo-sync 的同步水位线失效，会重复推送全部任务；
- 新增字段是安全的，两个消费者都会忽略未知字段。

联系人：todo-sync 维护者（移动端组）。
