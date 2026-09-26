---
title: todo-cli 模块
description: 项目内待办 CLI 的模块边界——CLI/核心/存储三职责切面、数据流与扩展约定
summary: 命令名 todo，uv 包零运行时依赖；CLI 解析 → 核心计算 → 存储整体读写；新子命令必须复用核心与存储层，不绕过直改文件
tags: [todo-cli, module, architecture, cli]
type: module
area: todo-cli
date: 2026-09-26
---

项目内待办 CLI，命令名 `todo`，uv 管理的 Python 包（Python >= 3.12，运行时零依赖，dev 仅 pytest）。

**边界**：单命令行入口 + 单 JSON 文件存储（见 [[decision/single-json-storage-and-id-policy]]）。无服务、无数据库、无 GUI、无同步。

**内部切面**（impl 可自定文件布局，但三职责保持可分）：

- **CLI 层**：argparse 子命令解析（add/list/done/reopen/rm/edit/clear），用法错误交给 argparse 非零退出。
- **核心层**：任务模型、next_id 分配、过滤叠加、排序规则（语义见 [[decision/list-semantics-narrowing-and-single-sort]]）。
- **存储层**：`./.todos.json` 读写、next_id 持久化、原子写入。

**数据流**：CLI 解析参数 → 核心层在内存列表上计算 → 存储层整体读入/整体写回（无增量写、无并发锁）。

**扩展约定**：新子命令挂进 CLI 层、复用核心层过滤排序与存储层写回；不绕过核心层直接操作文件。测试以临时目录为 cwd 隔离数据文件。
