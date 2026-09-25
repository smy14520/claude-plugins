---
title: ID 永不复用
description: Store 持久化自增 ID 计数器，rm 后跳号继续，绝不回收复用旧编号
type: decision
tags: [todo, storage]
---

# ID 永不复用

Store 中持久化 `next_id` 计数器，每次创建 Todo 自增分配；`rm` 之后编号跳号继续，绝不回收。**若复用（如取 max(id)+1），`todo done 5` 可能命中 rm 之后新出现的另一个 Todo——用户记忆与外部笔记里的旧 ID 引用会静默错位**，这是数据层面的错误行为而非美观问题。

## Consequences

- 编号会因删除出现空洞（1,2,4,7…），属预期行为，帮助文案需照常展示原编号；
- 计数器与 Todo 同存于 Store，存储格式见 spec。

## Revisit When

无需主动重估；仅当存储格式整体重写时一并重新设计。
