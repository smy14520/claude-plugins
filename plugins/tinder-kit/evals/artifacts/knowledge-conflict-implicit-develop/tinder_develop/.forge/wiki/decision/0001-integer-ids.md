---
title: todo 新任务使用 uuid4 作为 id
description: 新任务 id 用 uuid4；存量整数 id 原样保留不迁移，done 按字符串化匹配兼容两种
type: decision
tags: [storage, sync]
---

# todo 新任务使用 uuid4 作为 id

新任务的 `id` 使用 uuid4 字符串（`uuid.uuid4()`）。存量 `.todos.json` 里的整数 id 原样保留、不做一次性迁移；`done` 按字符串化相等匹配，两种 id 都能操作。

> 原为：id 使用单调递增整数（max+1），明确不用 uuid——因为手机端同步服务 todo-sync 以 `max(id)` 作为增量同步水位线。2026-09-29 废止：todo-sync 已升级为按 `updated_at` 同步，水位线依赖不复存在，经确认改为 uuid。
