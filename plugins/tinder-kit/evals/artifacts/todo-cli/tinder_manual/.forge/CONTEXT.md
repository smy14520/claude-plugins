# CONTEXT — 统一语言词汇表

本文件是项目唯一术语真实源（glossary）。只放术语定义与 `_Avoid_` 负面清单；
实现细节与规格进 `.forge/v1/spec.md`，架构决策进 `.forge/wiki/decision/`。

## Task（任务）

本项目的核心实体：一条待办事项。由整数 ID 唯一标识（文件内递增、删除后永不复用）。
允许重复标题。字段仅限：标题、标签、状态、创建/完成时间戳（无 due / priority / notes）。

_Avoid_: item, entry, record, memo, reminder

## Tag（标签）

Task 的唯一组织维度——本项目**没有** Project / List 概念。每条 Task 可有多个 Tag；
小写归一、去重、排序。Tag 无独立注册表，完全由 Task 派生：最后一个引用它的 Task
消失，Tag 即消失。过滤语义：多个 `--tag` 取交集（AND），`--tag a,b` 取并集（OR）。

_Avoid_: project, list, category, folder, label

## Pending（待办）

Task 的初始状态，尚未完成。`ls` 默认只显示 Pending。

_Avoid_: open, active, unchecked

## Done（完成）

Task 的完成状态（本版本无 archive / 软删概念）。迁移：`done`（Pending → Done，幂等）、
`reopen`（Done → Pending，幂等）。`rm` 是删除而非状态——被删的 Task 不复存在。

_Avoid_: finished, closed, checked, archived
