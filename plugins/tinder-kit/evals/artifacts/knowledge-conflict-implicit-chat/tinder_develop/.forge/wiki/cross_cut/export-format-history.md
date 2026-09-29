---
title: export 格式沿革：CSV（月报消费）→ JSON（无外部消费者）
type: cross_cut
tags: [export, report]
description: export 曾输出 CSV 供月报脚本 report_todos.py 消费；该脚本 2026-08 下线后，export 于 2026-09-29 改为输出 JSON 数组，现无外部消费者
anchors: [export]
---

# export 格式沿革：CSV（月报消费）→ JSON（无外部消费者）

## 原先：CSV（至 2026-09-28）

export 曾按列顺序（id, title, done）输出 CSV，`done` 为字符串 `"True"/"False"`、`id` 为字符串。这一格式专为运维机上的月度报表脚本 `report_todos.py`（不在本仓库）而设：它每月 1 号运行 `python3 todo.py export /tmp/todos.csv`，按列顺序读取结果统计完成率，因此当时改 export 格式或列顺序必须与该脚本联动。

## 为何变

`report_todos.py` 于 2026-08 下线，CSV 格式存在的原因随之消失。2026-09-29 export 改为输出 JSON 数组（每项 `{"id", "title", "done"}`，字段显式投影），不再有按列顺序的外部约束。

## 现状

export 输出 JSON 数组，无外部消费者。`id` 保持整数（与 [ADR-0001](../decision/0001-integer-ids.md) 一致，CSV 时代会退化为字符串）。新增字段追加在各项目末尾即可，无兼容性负担。
