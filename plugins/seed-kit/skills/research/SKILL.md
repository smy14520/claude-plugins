---
name: research
description: "给一个需求收集外部资料并整理成 AI 可读的工作区：竞品调研、外部 API 摸底、数据源与字段盘点。维护 .arbor/research/<topic>/（index.md / raw/ / notes/）。仅用户主动触发。"
---
# Research — 外部资料收集

通用约定见 [`../references/conventions.md`](../references/conventions.md)。

在需求冻结之前，把它的外部世界整理成后续可直接消费的资料。典型场景：做测评网站前调研竞品好在哪、数据可以抓哪些站、字段有哪些；接外部平台前摸清 API、鉴权和大致流程。

## 工作区（index-first）

```
.arbor/research/<topic>/
├── index.md   # 导航与结论：调研了什么、结论是什么、每份资料在哪
├── raw/       # 原始资料（抓取页面、API 文档摘录、响应样例）
└── notes/     # 整理后的可读笔记（对比表、字段清单、流程图）
```

- `index.md` 是唯一入口：后续 brainstorm 只读它就能定位一切。每收一份资料就更新 index。
- `raw/` 保留出处（URL + 抓取日期）；`notes/` 是从 raw 提炼的结论，注明依据哪些 raw。

## 工作方式

- 先和用户对齐调研问题与边界，再开始搜集；调研中发现的新关键问题先确认是否纳入。
- 只收集、核实、整理；不做设计决策、不写 PRD、不评判需求本身。
- 信息冲突或存疑时标注出来，不要替用户裁决。

## 停止

调研问题都有了有出处的回答、`index.md` 能让人一次读懂时停止。告知用户：brainstorm 时可以指定读这个 topic。不自动进入 brainstorm。
