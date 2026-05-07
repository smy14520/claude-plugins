# index.md 与根页面

`.wiki/` 支持嵌套目录与 wikilinks。不要依赖人工逐页扫描；先用 `sdd-arbor wiki-index/search/collect` 形成 JSON，再选择性读取页面。

## index.md

`.wiki/index.md` 是 Obsidian 入口页。只要创建或更新 wiki 页面，就应确保它存在，并至少链接到相关分组入口。

它可以列：

- 领域 root 页面
- Modules 入口
- CrossCut 入口
- 跨域 concepts / decisions
- source 页面
- orphan/待整理页面

不要在 `.wiki/index.md` 复制每个分组的全部子页面；重复导航会腐化。

## 分组 index.md

常用分组目录应有自己的 `index.md`，让 Obsidian 用户不用全局搜索：

- `.wiki/Modules/index.md`：链接 module note。
- `.wiki/CrossCut/index.md`：链接 `type: cross_cut` 页面。

分组 `index.md` 可以列该分组下的页面和一句用途说明；真实内容仍在具体页面。

## `.wiki/index.md` 推荐 section 模板

按 page type 分组，每条一行 wikilink + 一句用途。示例：

```markdown
# Wiki Index

## 概览
- [[Overview]] — 项目领域综述（如有）

## 模块（type: module）
- [[Modules/Todo core domain]] — Todo Task schema、生命周期 helper、localStorage adapter

## 跨模块同步改动（type: cross_cut）
- [[CrossCut/Todo 生命周期改动]] — 修改生命周期能力时同步检查的 5 处位置

## 决策（type: decision）
- [[Decisions/Local-only 数据架构]] — 第一版不引入云同步的取舍

## 概念 / 模式（type: concept）
- [[Concepts/Optimistic UI 更新模式]]

## 已知坑（type: gotcha）
- [[Gotchas/localStorage QuotaExceededError]]

## 外部资料（type: source）
- [[Sources/HTML5 storage spec]]

## 真实对象（type: entity）
- [[Entities/支付服务]]

## 待整理 / orphan
- [[Drafts/...]]
```

要点：

- 每次 ingest 后同步更新对应 section（一行一个 wikilink，附一句话用途）。
- **不在 `index.md` 里复制每个 root 的所有子页面** —— 重复导航会腐化（AP4）。
- 空 section 可以省略；不需要为了"齐全"塞占位。
- LLM 检索时可直接 `cat .wiki/index.md` 拿全 wiki 目录（小-中规模 wiki 不需要 helper），再按需 drill down。

## 根页面

根页面是领域枢纽。适合在一个领域已有多个 module/entity/decision/gotcha 时创建。

推荐 frontmatter：

```yaml
---
title: <领域名>
description: <中文一行检索提示>
tags: [root, <domain>]
type: entity
summary: <中文紧凑摘要>
---
```

根页面应按使用意图组织 links：模块、关键决策、常见坑、外部资料、相关 source。

## Modules 根页面

项目有多个完成 package 后，可创建 `.wiki/Modules.md` 或 `.wiki/Modules/index.md`：

```markdown
# 模块

- [[余额账本]] — 余额账户、充值、扣款、退款 contract
- [[用户角色访问]] — 用户/讲师/管理员权限边界
```

Module note 的真实内容在 `.wiki/Modules/<中文标题>.md`；retrieval helper 会扫描嵌套页面，所以目录结构不需要额外配置。

## 链接规则

- 页面间用 `[[Page]]` 或 `[[Page|Alias]]`。
- Package PRD 可链接 wiki 作为背景提示。
- Package PRD 的执行边界必须自包含；不要要求实现者跟随 wikilink 才知道要做什么。
- Module locator 不用行号；使用 path + stable symbol。
