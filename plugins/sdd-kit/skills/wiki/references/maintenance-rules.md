# Wiki 维护规则

`.wiki/` 是项目本地导航层，不是 source of truth。维护目标是让后续 AI/人类能快速判断哪些页面值得细读，同时避免旧页面伪装成当前事实。

## R1 — 页面必须可检索

每个页面应有 frontmatter：

```yaml
---
title: <中文标题>
description: <中文一行检索提示>
tags: [<domain>, ...]
type: entity | concept | gotcha | decision | source | module
summary: <中文紧凑摘要>
---
```

`description` 用来让 `wiki-index/search/collect` 快速判断相关性；`summary` 用来减少主会话盲读。

不要把隐藏目录（如 `.arbor/`、`.claude/`、`.git/`）里的原始文件、workflow 状态快照或规则配置整理成 wiki 页面；这些目录本身是 source of truth 或工具配置。明确 helper 输出（如 `sdd-arbor module-summary <package> --json`）除外。

## R2 — index.md 只做入口

`index.md` 不是全量目录。它只列：

- 领域 root 页面
- Modules 入口
- 跨域 concepts / decisions
- source 页面
- orphan/待整理页面

不要把每个 root 的子页面都复制到 `index.md`；重复导航会腐化。

## R3 — 根页面按领域自然生成

当一个领域已有多个 module/entity/decision/gotcha 时，可以创建 root 页面。根页面按使用意图组织 wikilinks：模块、关键决策、常见坑、外部资料、相关 source。

不要为了分类创建空壳 root；没有稳定使用场景时，让页面先保持普通 note。

## R4 — Module note 不写行号

Module note 来自 `sdd-arbor module-summary <package> --json` 的稳定 packet，再由 wiki skill/subagent 写入 `.wiki/Modules/<中文标题>.md`。

定位使用 stable locators：

- file path + class/function/method name
- route name / API operation id
- table / index / migration id
- config key / env key
- test name
- contract request id

不要写 line numbers；行号会随代码变化快速失效。

## R5 — Query 先用 helper，再读页面

检索流程：

```text
sdd-arbor wiki-collect --query "<query>" --limit 5 --json
```

先看 selected summaries、tags、links/backlinks、locators，再只读取真正相关页面。用于实现或 review 时，必须再验证当前代码和 `.arbor` 状态。

## Lint 建议

Lint 可以报告和建议，不能擅自删除页面。重点检查：

- 缺失 `description` / `summary` / `tags`
- broken wikilinks
- orphan pages
- 重复主题
- module note 缺少 `package` / `source_checkpoint`
- locator 出现 line number
- 明显过时但未标记的页面

旧页面默认是“需要验证”，不是“自动失效”。若页面仍有效，可更新摘要或补充 verification note；若失效，显式标记 deprecated 或由用户决定删除。