---
name: wiki
description: "维护项目的 .wiki/ 知识层：收录值得长期保留的资料与多文件链路知识，随代码更新，用 seed wiki index/search/collect/lint 查询与体检。仅用户主动触发。"
---
# Wiki — 项目知识层

通用约定见 [`../references/conventions.md`](../references/conventions.md)。

`.arbor/.wiki/` 承载项目与 AI 一同成长的知识：用户觉得有长期价值的 research 资料、以及"改 X 要动哪几处"的多文件链路。它是导航层，不是 source of truth——定位之后必须验证当前代码。

## 目录结构

```
.arbor/.wiki/
  index.md          ← 按 type 分组的索引（由 seed wiki index --write 生成）
  log.md            ← 变更日志（自动维护）
  gotcha/           ← 实现陷阱
  cross_cut/        ← 跨文件修改链路
  decision/         ← 设计决策
  entity/           ← 实体
  concept/          ← 概念
  source/           ← 外部资料
  module/           ← 模块
```

页面文件放进对应 type 的子目录。`index.md` 和 `log.md` 始终在根目录下。

## 页面模型

frontmatter 必填：

- `title` — 页面标题
- `description` — 何时该读此页（写场景不写主题，让 agent 能自然命中）
- `type` — 封闭集：`entity` / `concept` / `gotcha` / `decision` / `source` / `module` / `cross_cut`
- `area` — 自由轴，按项目领域自然划分
- `confidence` — `high`（代码实锤）/ `medium`（推断）/ `low`（不确定）
- `last_updated` — 最后更新日期（YYYY-MM-DD）

页面里指向代码用 `文件路径#符号名`（符号锚：存符号不存行号，显示时 `seed wiki index --resolve` 实时转行号，`seed wiki lint` 验证符号是否存在）。避免旧式 `文件:行号`——会随代码漂移失效。互相引用用 `[[../gotcha/页面名]]`（跨目录的相对 wikilink）。

## 操作

- **收录（ingest）**：用户指明来源（research 资料、对话结论、某次排坑过程）→ 每发现一个独立知识点写一页。链路类页面按"入口 → 要改的每一处 → 注意什么"组织，写明当下的代码位置。
  **涟漪更新**：写完新页后，扫描已有页面——找到主题相关的页，在相关页里补 `[[新页面]]` 引用。如果新发现和已有页面矛盾，在旧页标注 `confidence: low` 并注明冲突，不直接覆盖。
  全部收录完跑 `seed wiki index --write`——生成 `index.md`（按 type 分组索引）和 `log.md`（变更日志）。

- **更新（update）**：对照当前代码逐条核对页面引用，修正失效的符号锚（`seed wiki lint` 会标出文件不存在/符号找不到的锚点）；代码已变而页面没变是 wiki 最大的失效模式。更新后跑 `seed wiki index --write` 刷新索引和日志。

- **查询**：先看 `index.md` 扫类型→挑相关页；看 `log.md` 了解最近变更。精确检索用 `seed wiki search "<query>"` / `seed wiki collect --query "<query>" --limit 5 --json`。

- **体检**：`seed wiki lint --json`——断链、缺 frontmatter、孤儿页、行号 locator 漂移、低置信度页面过期提醒。

## 边界

- 用户触发 wiki skill 时做**集中收录、批量更新、体检**（ingest / update / lint）。
- brainstorm、impl、review 入场时各自加载 `seed wiki index --json` 暖场，收尾时按阶段职责写入——这些是各阶段的内部动作，不叫「触发 wiki skill」。
- 不收录代码本身能直接回答的事实（函数签名、单文件实现细节）；收录的是跨文件、易遗忘、有"为什么"的知识。
- 与 `.arbor/` 无依赖：wiki 跟项目走，不跟任务走。
