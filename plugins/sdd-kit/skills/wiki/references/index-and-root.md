# index.md 与根页面

`.wiki/` 支持嵌套目录与 wikilinks。不要依赖人工逐页扫描；先用 `sdd-arbor wiki-index/search/collect` 形成 JSON，再选择性读取页面。

## index.md

`index.md` 是轻量入口，不是全量目录。它可以列：

- 领域 root 页面
- Modules 入口
- 跨域 concepts / decisions
- source 页面
- orphan/待整理页面

不要在 `index.md` 复制每个 root 的全部子页面；重复导航会腐化。

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
- `task.md` 不应依赖 wikilinks；执行计划必须自包含。
- Module locator 不用行号；使用 path + stable symbol。
