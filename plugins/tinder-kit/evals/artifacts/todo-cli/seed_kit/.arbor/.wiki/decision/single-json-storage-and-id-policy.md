---
title: 存储定死单文件 JSON，ID 用 next_id 单调计数器
description: todo-cli 存储层铁律——单文件 ./.todos.json、next_id 持久计数保证 ID 永不回收、temp+replace 原子写、错误操作不动文件
summary: 存储只有单文件 JSON；next_id 是持久单调计数器而非 max+1；写入必须原子替换；错误不改磁盘字节
tags: [todo-cli, storage, json, atomic-write, id-policy]
type: decision
area: todo-cli
date: 2026-09-26
---

todo-cli 的存储只有当前目录下单一 `./.todos.json`，任何 task 都不引入 SQLite/数据库/多文件分片（用户明确拍板"坚决不要任何数据库"）。文件顶层是 `{"next_id": int, "todos": [record...]}`。

关键取舍与推论：

- **next_id 是持久化单调计数器，不是 max(id)+1。** "ID 删除后不回收"在空列表下会退化：若用 max(id)+1，rm/clear 删光后新任务会重新拿到 1，与历史引用冲突。任何新命令（导出、批量操作、未来 sync）读写文件时都必须原样保留 next_id、只增不减。
- **record 字段是定版契约**：id/title/tags/priority(high|med|low)/done/created_at/completed_at。加功能加字段可以，改已有字段语义不行——文件是用户 git 里的资产，格式漂移等于数据破坏。
- **写入必须走 temp 文件 + `os.replace` 原子替换**。.todos.json 是用户手工编辑和 git 管理的对象，半写状态比功能缺失严重得多。新写入路径（import/export 等）沿用同一模式。
- **错误操作不动文件**：引用不存在 id、状态不满足（done 已完成任务/reopen 未完成任务）一律非零退出 + stderr，磁盘字节不变——文件可当审计日志用。
- **读取宽容、写入收敛**：文件缺失视为空列表且不创建文件（仅写操作落盘），`list` 在干净仓库里不留垃圾。
