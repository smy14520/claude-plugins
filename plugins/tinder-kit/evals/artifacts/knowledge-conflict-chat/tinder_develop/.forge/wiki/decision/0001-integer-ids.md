---
title: todo id 使用单调递增整数
description: id 必须是递增整数，因为手机端同步服务 todo-sync 以 max(id) 作为同步水位线
type: decision
tags: [storage, sync]
---

# todo id 使用单调递增整数

todo 的 `id` 使用单调递增整数，不使用 uuid。手机端同步服务 todo-sync（另一个仓库）每 5 分钟读取 `.todos.json`，以 `max(id)` 作为增量同步水位线；换成无序 id 会让它重复推送全部任务。
