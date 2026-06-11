# 操作：Ingest / Query / Module Publish / Lint

Wiki 默认根目录是项目内 `.wiki/`。它是 orientation/index layer，不是 source of truth；改代码前仍要验证当前代码和 `.arbor`。

---

## Ingest

将用户显式要求保存的新知识写成 `.wiki/**/*.md` 页面。

### 流程

1. 先排除隐藏目录来源：不把 `.arbor/`、`.claude/`、`.git/` 等隐藏目录里的原始文件、workflow 状态快照或规则配置整理成 wiki 页面；需要时直接读取 source of truth。明确 helper 输出（如 `sdd-arbor module-summary <package> --json`）除外。
2. 分类：`module | cross_cut | entity | concept | gotcha | decision | source`。
3. 确定页面路径：按项目目录自然组织，可嵌套；推荐 `module` 放 `.wiki/Modules/`，`cross_cut` 放 `.wiki/CrossCut/`。
4. 先运行 `sdd-wiki index --json` 检查是否已有近似页面。
5. 已存在时优先追加/合并；只有主题独立时新建。
6. 写 frontmatter：`title`、`description`、`tags`、`type`、`summary`、`last_updated`。
7. 使用 wikilinks 连接相关页面。
8. 维护 Obsidian 导航：确保 `.wiki/index.md` 存在；若写入 module note，更新 `.wiki/Modules/index.md`；若写入 cross_cut 页面，更新 `.wiki/CrossCut/index.md`。
9. 若写入的是 module note，不写行号；使用 stable locators。
10. 可追加 `.wiki/log.md`；推荐统一前缀格式以便 `grep '^## \[' .wiki/log.md | tail -20` 快速拿时间线：

    ```markdown
    ## [YYYY-MM-DD] ingest | <页面标题或路径>
    ## [YYYY-MM-DD] lint | warnings: <n>, errors: <n>
    ## [YYYY-MM-DD] supersede | [[Old Decision]] -> [[New Decision]]
    ```

    log 写入失败不阻塞知识记录。

### Frontmatter 最小契约

```yaml
---
title: <中文标题>
description: <中文一行检索提示>
tags: [<domain>, ...]
type: module | cross_cut | entity | concept | gotcha | decision | source
summary: <中文紧凑摘要>
last_updated: YYYY-MM-DD
---
```

`last_updated` 记录页面**最近一次实质内容修改**的日期（`YYYY-MM-DD`）。每次 ingest / merge / supersede 同步更新；纯排版微调可不更新。该字段让 Obsidian Dataview 能查“近 30 天更新的 cross_cut”，也是未来 stale 检测的基础。

---

## Query

只读检索。优先使用 helper，避免主会话逐页盲读：

```text
sdd-wiki collect --query "<query>" --limit 5 --json
```

Wiki 查询采用渐进式披露：先看候选页面的 title、description、summary、tags、type、links/backlinks 和 locators，再只读取当前任务真正需要的页面全文。

流程：

1. `sdd-wiki collect` 获取 selected summaries、paths、tags、links/backlinks、locators。
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
2. 读取 packet 中 `package`、`slices`、`contracts`、`important_files`、`tests`、`implementation`、`verification`；`related_packages` 只有明确元数据时才使用。
3. 写/更新 `.wiki/Modules/<中文标题>.md`。
4. 保留人工补充内容，更新来自 arbor 的 summary / slices / contracts / verification sections。
5. 不写行号；locator 使用 path + symbol/route/table/config/test/contract id。
6. 返回更新页面路径和摘要。

---

## Lint

审计 `.wiki` 健康度。只读报告，可以建议，不能擅自删除或 auto-fix。

```text
sdd-wiki lint --json
```

首版检查 metadata、broken wikilinks、重复 title/stem/module package、orphan warning、隐藏路径污染和 module line-number locator。
