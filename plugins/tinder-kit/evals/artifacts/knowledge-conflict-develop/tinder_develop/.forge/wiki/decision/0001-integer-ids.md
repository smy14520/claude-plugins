---
title: todo id 使用 uuid，同步水位线为 updated_at
description: 新增 todo 用 uuid4，存量整数 id 保留；todo-sync 按 updated_at 做增量同步
type: decision
tags: [storage, sync]
---

# todo id 使用 uuid，同步水位线为 updated_at

新增 todo 的 `id` 使用 `uuid.uuid4()`；每条记录携带 `updated_at`（ISO 8601 UTC 字符串，含微秒），手机端同步服务 todo-sync（另一个仓库）自 2026-09-22 当周升级后按 `updated_at` 做增量同步水位线。存量记录保留旧整数 id，不做迁移改写；`done` 同时接受完整 uuid、uuid 唯一前缀和旧整数 id。存量记录缺失的 `updated_at` 由读取方以 epoch 回填（视作从未修改，避免换水位线时全量重推）。

原为递增整数、因 todo-sync 改按 updated_at 同步而改。
