---
name: wiki
description: "Manage the project's persistent knowledge wiki at `.wiki/` — project-local Obsidian-style markdown with wikilinks, frontmatter descriptions, and deterministic arbor wiki-index/wiki-search/wiki-collect retrieval. Also publishes completed sdd-kit module-summary packets into module notes. Invoke only on explicit user request (e.g. '用 wiki skill ingest/query/lint/module-summary …')."
---

# Wiki — project-local knowledge layer

使用语言：中文。写入 `.wiki/**/*.md` 的正文、标题、章节标题、`description` 和 `summary` 默认中文；代码标识符、文件路径、命令和 schema 字段保持原样。

将项目根目录下的 `.wiki/` 作为持久化知识库。它是 orientation/index layer，不是 source of truth：用来快速定位模块事实、契约、关键文件和历史决定；真正改代码前仍要验证当前代码和 `.arbor` 状态。

sdd-kit 不耦合 Obsidian。它只产出 deterministic packets 和 retrieval JSON；wiki skill/subagent 负责把这些信息写成 Obsidian-style markdown note。

## 定位

```text
.arbor/                    # workflow/source-of-truth state
.wiki/                     # project-local knowledge/navigation layer
code...                    # implementation source of truth
```

- `.arbor/tasks/<package>`：package lifecycle、PRD、task、review、context。
- `sdd-arbor module-summary <package> --json`：稳定 module summary packet。
- `.wiki/**/*.md`：面向后续 AI/人类的摘要、链接、stable locators。
- `sdd-arbor wiki-index/search/collect`：低上下文检索入口。

## 三个原语

### Ingest — 提炼新知识

用户显式要求“记一下/沉淀/wiki ingest”时执行。页面默认写到 `.wiki/`，frontmatter 至少包含：

```yaml
---
title: <中文标题>
description: <中文一行检索提示>
tags: [<domain>, ...]
type: entity | concept | gotcha | decision | source | module
summary: <中文紧凑摘要>
---
```

已有页面优先追加/合并；不为了分类创建空壳页面。

不把隐藏目录（如 `.arbor/`、`.claude/`、`.git/`）里的原始文件、workflow 状态快照或规则配置整理成 wiki 页面；需要查询时直接读 source of truth。例外是明确的 helper 输出，例如 `sdd-arbor module-summary <package> --json` 生成的稳定 packet。

### Query — 检索已有知识

优先使用 arbor retrieval，而不是逐页 blind read：

```text
sdd-arbor wiki-collect --query "balance refund" --limit 5 --json
```

流程：

1. `wiki-index` 或 `wiki-collect` 生成 JSON：title/path/tags/description/summary/links/backlinks/locators。
2. 选择 1-5 个真正相关页面读取。
3. 返回已读页面、关键发现、仍需验证的源文件/`.arbor` 状态。

检索/写 note 通常交给 subagent，避免污染主会话上下文；subagent 只返回 selected summaries 和路径。

### Module summary publish — 发布完成模块卡片

当 package 到达稳定 milestone（例如 completed/merged）后，可请求 wiki skill/subagent：

```text
sdd-arbor module-summary <package> --json
```

subagent 根据 packet 写/更新 `.wiki/Modules/<中文标题>.md`。推荐结构：

```markdown
---
title: 余额账本
description: 余额账户、流水、充值、扣款、退款和幂等 contract
tags: [module, backend, ledger]
type: module
package: balance-ledger
source: arbor
source_checkpoint: <sha>
summary: <中文紧凑摘要>
---

# 余额账本

## 摘要
## 对外契约
## 关键文件与稳定定位
## 不变量
## 测试
## 相关模块
## 验证记录
```

不要写行号。定位使用 stable locators：file path + class/function/method/route/table/index/config key/test name/contract id。

### Lint — 审计 wiki 健康状况

Lint 可结合 `wiki-index` 检查：broken links、orphan pages、缺失 description/summary、过期 notes、重复主题。Lint 可以报告和建议，但不要擅自删除页面。

## 目录结构

```text
.wiki/
├── index.md
├── log.md
├── Modules/
│   └── <模块标题>.md
├── Decisions/
├── Concepts/
├── Gotchas/
└── Sources/
```

目录可按项目自然演化；retrieval 会扫描 `.wiki/**/*.md`，所以不要求扁平结构。

## Retrieval helpers

```text
sdd-arbor wiki-index --json
sdd-arbor wiki-index --tag module --json
sdd-arbor wiki-search "balance refund" --json
sdd-arbor wiki-collect --query "balance refund" --limit 5 --json
```

- `wiki-index`：列出 metadata + links/backlinks + locators。
- `wiki-search`：确定性 token scoring，不用 embedding。
- `wiki-collect`：给 AI 的 compact selected summaries。

## 核心规则

1. `.wiki` 是导航层，不是 source of truth。
2. 每页必须有 `description`；最好也有 `summary` 和 `tags`。
3. 模块 note 不用行号；使用 stable locators。
4. 子页面和 nested wikilinks 可以自由存在；retrieval helper 负责索引，不要让主会话逐页盲读。
5. Module summary 由 `.arbor` milestone 触发更可靠；hook 最多提醒，不承担语义发布。
6. 写 wiki 通常用 subagent；主会话只消费结果摘要和路径。

## 本 skill 不做

- 不自动改代码。
- 不把 wiki 内容当成未验证事实直接用于实现。
- 不执行向量搜索或 embedding 检索。
- 不在每次文件修改后自动重写 wiki。
- 不把 `.wiki` 写到 `.arbor/wiki`，除非用户显式覆盖。
