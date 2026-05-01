---
name: wiki
description: "Manage the project's `.wiki/` orientation layer: ingest explicit knowledge, query with deterministic wiki-index/search/collect, lint wiki health, and publish sdd-arbor module-summary packets. Invoke only on explicit user request (e.g. '用 wiki skill ingest/query/lint/module-summary …')."
---

# Wiki — project-local knowledge layer

使用语言：中文。写入 `.wiki/**/*.md` 的正文、标题、章节标题、`description` 和 `summary` 默认中文；代码标识符、路径、命令和 schema 字段保持原样。

`.wiki/` 是 orientation/index layer，不是 source of truth。它帮助后续 AI/人类快速定位背景、module note、stable locators 和历史决定；用于实现或 review 前必须验证当前代码和 `.arbor`。

## 读写边界

```text
.arbor/   # workflow source of truth
.wiki/    # navigation / knowledge layer
code      # implementation source of truth
```

- 不把隐藏目录（如 `.arbor/`、`.claude/`、`.git/`）里的原始文件、workflow 状态快照或规则配置整理成 wiki 页面。
- 例外：明确稳定 helper 输出，例如 `sdd-arbor module-summary <package> --json`。
- 不自动改代码，不把 wiki 内容当成未验证事实，不自动 ingest 每次改动。

## 原语

### Ingest

用户显式要求“记一下 / 沉淀 / wiki ingest”时，把新知识写成 `.wiki/**/*.md` 页面。

流程详见 `references/operations.md`；页面 schema 与 module note 结构详见 `references/page-types.md`。

### Query

优先用 helper，避免逐页 blind read：

```text
sdd-arbor wiki-collect --query "<query>" --limit 5 --json
```

只读取真正相关页面。若结果用于实现或 review，必须再验证当前代码和 `.arbor`。

### Module publish

package 到达稳定 milestone 后：

```text
sdd-arbor module-summary <package> --json
```

根据 packet 写/更新 `.wiki/Modules/<中文标题>.md`。Module locator 不写行号，只写 path + stable symbol/route/table/config/test/contract id。

### Lint

```text
sdd-arbor wiki-lint --json
```

只读报告 `.wiki` 健康度；可以建议，不自动修复或删除页面。

## References

- `references/page-types.md` — 页面 schema、module note 结构、stable locators。
- `references/operations.md` — ingest/query/module publish/lint 操作流程。
- `references/index-and-root.md` — `index.md` 与领域 root 页面。
- `references/anti-patterns.md` — wiki 反模式。
- `references/maintenance-rules.md` — 维护 checklist。
