---
name: wiki
description: "Manage the project's `.wiki/` orientation layer: ingest explicit knowledge, query with sdd-wiki index/search/collect, lint wiki health, and publish module summaries. Invoke only on explicit user request."
---

# Wiki — project-local orientation layer

通用约定见 [`../references/conventions.md`](../references/conventions.md)。写入 `.wiki/**/*.md` 的正文、标题、章节标题、`description` 和 `summary` 默认中文；代码标识符、路径、命令、schema 字段保持原样。

`.wiki/` 是 orientation / index layer，帮助 AI / 人类快速定位背景、module 契约、历史决定。改代码或 review 前必须验证当前代码和 `.arbor`——wiki 不是 source of truth。

```text
.arbor/   # workflow source of truth
.wiki/    # navigation / knowledge layer  ← 本 skill 负责
code      # implementation source of truth
```

## Hard rules

1. 用户显式要求才 ingest / 写 wiki；不自动摄入每次变更。
2. 不把 `.arbor/` / `.claude/` / `.git/` 等隐藏目录的原始文件整理成 wiki 页面（helper 稳定输出例外）。
3. 每页 frontmatter 必须有 `title` / `description` / `type`；建议有 `summary` / `tags` / `last_updated`。
4. Module note 不写行号；locator 用 path + stable symbol / route / table / config / test / contract id。
5. Query 前先用 `sdd-wiki collect`，看 summary / tags / links 再决定读哪些页面全文。
6. 实现或 review 前把 wiki 信息回代码和 `.arbor` 验证一次。

## 自适应组织（按项目画像派生 area）

页面有两个正交轴：

- `type`（结构轴，封闭集合）：页面如何被机器和流程消费，跨项目不变。
- `area`（领域轴，自由值）：页面属于**这个项目**架构的哪一块，按项目画像派生，不硬套模板。

首次为项目建 wiki（或 area 明显缺失）时，先推断项目画像（参考 brainstorm 的 `references/technical-framing.md` 画像表），再从项目实际架构派生 3-8 个 area。示例方向：web → 权限 / 数据模型 / 集成 / 管理面；game → 渲染循环 / 资产管线 / 输入 / 存档 / 性能；cli → 命令契约 / 输出格式 / 分发；不匹配画像时从代码顶层结构派生。area 是导航用的软分类：用 `.wiki/index.md` 按 area 分组列页面，不为每个 area 强建目录；项目演化时合并或重命名 area，宁缺勿滥。

## Ingest（用户说「记一下 X」/「wiki ingest」）

1. 分类 `type`：`module` / `cross_cut` / `entity` / `concept` / `gotcha` / `decision` / `source`；再判断 `area`（见上）。
2. 路径：`module` → `.wiki/Modules/`；`cross_cut` → `.wiki/CrossCut/`；其它可按项目目录自然组织。
3. `sdd-wiki index --json` 检查是否已有近似页面：已存在优先合并，主题独立时新建。
4. 写 frontmatter（见下）+ 正文 + wikilinks 连接相关页面。
5. 维护导航：确保 `.wiki/index.md` 存在并按 area 分组；module note 更新 `.wiki/Modules/index.md`；cross_cut 更新 `.wiki/CrossCut/index.md`。
6. 可追加 `.wiki/log.md` 一行（`## [YYYY-MM-DD] ingest | <页面>`）。

### Frontmatter 最小契约

```yaml
---
title: <中文标题>
description: <中文一行检索提示>
tags: [<domain>, ...]
type: module | cross_cut | entity | concept | gotcha | decision | source
area: <本项目的领域分区，如 渲染管线 / 权限 / 资产管线；自由值>
summary: <中文紧凑摘要>
last_updated: YYYY-MM-DD
---
```

页面类型 schema、stable locators、PRD 引用 wiki 的三层结构详见 [`references/page-types.md`](references/page-types.md)。

## Query

```bash
sdd-wiki collect --query "<keyword>" --limit 5 --json
```

渐进式披露：先看候选页的 title / description / summary / tags / type / links / backlinks / locators，只读真正相关的页面全文。输出：已读页面、关键发现、可用 locators、需要验证的代码 / `.arbor` 位置。

推荐由 subagent 执行 query；subagent 返回 compact result，主会话不吸收全量 wiki。

## Module publish

package 达到稳定 milestone 或 PRD amendment accepted 后：

```bash
sdd-arbor module-summary <package> --json
```

读 packet 中 package / slices / contracts / important_files / tests / implementation / verification 写或更新 `.wiki/Modules/<中文标题>.md`；`related_packages` 只在有明确元数据时使用。保留人工补充内容，只更新来自 arbor 的 summary / contract / verification sections。

## Lint

```bash
sdd-wiki lint --json
```

只读报告：metadata / broken wikilinks / 重复 title / stem / module package / orphan / 隐藏路径污染 / module 使用行号 locator。可以建议，不自动删除或修复页面。

## References

- `references/page-types.md` — 页面 schema、module note 结构、stable locators、PRD 引用范式。
- `references/operations.md` — ingest / query / publish / lint 详细操作流程。
- `references/index-and-root.md` — `.wiki/index.md` 与领域 root 页面结构。
- `references/anti-patterns.md` — wiki 反模式。
- `references/maintenance-rules.md` — 维护 checklist。
