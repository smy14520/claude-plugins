---
title: Wiki Index
description: 项目知识导航——按类型分组的 wiki 页面索引
type: index
---

# Wiki Index

## decision

- [list 语义：过滤即收窄（AND）+ 全视图唯一排序](decision/list-semantics-narrowing-and-single-sort.md) — todo-cli list 契约——多标签 AND 收窄、条件交集、全视图共用唯一排序、文本与 JSON 同源、stdout 纯净、空结果非错误
- [存储定死单文件 JSON，ID 用 next_id 单调计数器](decision/single-json-storage-and-id-policy.md) — todo-cli 存储层铁律——单文件 ./.todos.json、next_id 持久计数保证 ID 永不回收、temp+replace 原子写、错误操作不动文件

## module

- [todo-cli 模块](module/todo-cli.md) — 项目内待办 CLI 的模块边界——CLI/核心/存储三职责切面、数据流与扩展约定

