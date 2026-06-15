---
name: wiki
description: "维护项目的 .wiki/ 知识层：收录值得长期保留的资料与多文件链路知识，随代码更新，用 seed wiki index/search/collect/lint 查询与体检。仅用户主动触发。"
---
# Wiki — 项目知识层

通用约定见 [`../references/conventions.md`](../references/conventions.md)。

`.wiki/` 承载项目与 AI 一同成长的知识：用户觉得有长期价值的 research 资料、以及"改 X 要动哪几处"的多文件链路（例如加一种导出格式要在四五个文件里加枚举）。它是导航层，不是 source of truth——定位之后必须验证当前代码。

## 页面模型

两个正交轴（由 `seed wiki` CLI 索引，frontmatter 必填 title / description / type）：

- `type` 封闭集：`entity` / `concept` / `gotcha` / `decision` / `source` / `module` / `cross_cut`。多文件链路用 `cross_cut`，外部资料收录用 `source`，坑用 `gotcha`。
- `area` 自由轴：按当前项目的领域自然划分（游戏项目可能是 渲染/玩法/资产，web 项目可能是 前端/接口/权限）。不预设全局分类，跟项目长。

页面里指向代码用 `文件路径:行号` 或符号名；互相引用用 `[[页面名]]`。

## 操作

- **收录（ingest）**：用户指明来源（research 资料、对话结论、某次排坑过程）→ 写成一页：链路类页面按"入口 → 要改的每一处 → 注意什么"组织，写明当下的代码位置。
- **更新（update）**：对照当前代码逐条核对页面引用，修正失效的路径/行号/结论；代码已变而页面没变是 wiki 最大的失效模式。
- **查询**：`seed wiki search "<query>"` / `seed wiki collect --query "<query>" --limit 5 --json`。
- **体检**：`seed wiki lint --json`——断链、缺 frontmatter、孤儿页、行号 locator 漂移。

## 边界

- 只在用户明确要求时收录/更新/查询；不自动在其它 skill 流程中触发。
- 不收录代码本身能直接回答的事实（函数签名、单文件实现细节）；收录的是跨文件、易遗忘、有"为什么"的知识。
- 与 `.arbor/` 无依赖：wiki 跟项目走，不跟任务走。
