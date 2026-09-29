---
title: export 输出 JSON 数组（原 CSV 消费方 report_todos.py 已下线）
type: cross_cut
tags: [export, report]
description: export 自 2026-09 输出 JSON（id/title/done）；唯一外部消费方 report_todos.py 已于 2026-08 下线，当前无外部消费方
anchors: [export]
---

# export 输出 JSON 数组（原 CSV 消费方已下线）

**现状**：`python3 todo.py export <path>` 输出 JSON 数组，每项固定含 `id`、`title`、`done` 三个字段。当前仓库内外均无已知消费方，改格式暂无联动约束。

## 历史（原记录，2026-08 前有效）

运维机上的月度报表脚本 `report_todos.py`（不在本仓库）曾每月 1 号运行 `python3 todo.py export /tmp/todos.csv`，并按**列顺序**（id, title, done）读取 CSV 统计完成率。当时的规则是：改 export 的输出格式或列顺序 → 必须同步修改 `report_todos.py`；新增列只能追加在末尾。

## 变更记录

2026-08 该脚本下线，上述约束解除；2026-09 export 改为输出 JSON。若在运维机上发现残留的 `/tmp/todos.csv` 或仍按 CSV 解析 todo 导出的旧脚本，皆源于此历史，可安全清理。
