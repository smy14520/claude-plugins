# 操作：Ingest / Query / Module Publish / Lint

Wiki 默认根目录是项目内 `.wiki/`。它是 orientation/index layer，不是 source of truth；改代码前仍要验证当前代码和 `.arbor`。

---

## Ingest

将用户显式要求保存的新知识写成 `.wiki/**/*.md` 页面。

### 流程

1. 分类：`entity | concept | gotcha | decision | source | module`。
2. 确定页面路径：按项目目录自然组织，可嵌套；不要为了分类强制扁平。
3. 先运行 `sdd-arbor wiki-index --json` 检查是否已有近似页面。
4. 已存在时优先追加/合并；只有主题独立时新建。
5. 写 frontmatter：`title`、`description`、`tags`、`type`、`summary`。
6. 使用 wikilinks 连接相关页面。
7. 若写入的是 module note，不写行号；使用 stable locators。
8. 可追加 `.wiki/log.md`，但不要因为 log 失败阻塞知识记录。

### Frontmatter 最小契约

```yaml
---
title: <Title>
description: <one-line retrieval hook>
tags: [<domain>, ...]
type: entity | concept | gotcha | decision | source | module
summary: <compact summary>
---
```

---

## Query

只读检索。优先使用 helper，避免主会话逐页盲读：

```text
sdd-arbor wiki-collect --query "<query>" --limit 5 --json
```

流程：

1. `wiki-collect` 获取 selected summaries、paths、tags、links/backlinks、locators。
2. 只读取真正相关页面。
3. 输出：已读页面、关键发现、可用 locators、需要验证的代码/`.arbor` 位置。
4. 如果用于实现或 review，必须验证当前代码或 `.arbor`。

推荐由 subagent 执行 Query；subagent 返回 compact result，主会话不吸收全量 wiki。

---

## Module Publish

package 到达稳定 milestone 后发布模块卡片。

触发建议：

- package completed / merged
- PRD amendment accepted 后需要更新已有模块 note

流程：

1. 运行：`sdd-arbor module-summary <package> --json`。
2. 读取 packet 中 package、contracts、tests、related packages。
3. 写/更新 `.wiki/Modules/<Title>.md`。
4. 保留人工补充内容，更新来自 arbor 的 summary/contract/verification sections。
5. 不写行号；locator 使用 path + symbol/route/table/config/test/contract id。
6. 返回更新页面路径和摘要。

---

## Lint

审计 `.wiki` 健康度。可以报告和建议，不能擅自删除。

检查：

- 缺失 `description` / `summary` / `tags`。
- broken wikilinks。
- orphan pages。
- 重复主题。
- module note 是否缺少 package/source_checkpoint。
- locator 是否出现 line number（应移除）。

可用 `sdd-arbor wiki-index --json` 作为基础索引。
