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
- `confidence` — `high`（代码实锤）/ `medium`（推断）/ `low`（不确定）。新页面默认 `high`；被质疑或发现跟代码偏离时降级。`low` + 30 天未更新 = lint 警告「建议验证或归档」。
- `last_updated` — 最后更新日期（YYYY-MM-DD）。每次对照代码核实后刷新。

**页面生命周期**：`high → medium → low → 归档`。新页面从 `high` 起步，发现矛盾时降为 `low` 并注明冲突（不直接删除——保留错误记录也是知识）。`seed wiki lint` 会提醒过期低置信页。

## 收录标准

**写之前先问：这个信息在代码里能直接读到吗？** 能 → 不写。wiki 存的是代码说不清的东西。

必收（至少满足一）：
- **代码读不出的 why**：为什么这么设计、当时否决了什么替代方案、有什么隐藏契约（不变量、时序假设）
- **散在 3+ 文件里的横切**：改 X 要动 A/B/C，每处的角色和注意什么
- **踩了坑才知道的**：真 bug、反直觉行为、静默失效、不应该复用看似相似的既有模式的原因

不收：
- 代码结构概述（模块有哪些、文件在哪——读代码/目录就知道）
- 教科书式教程（how to add X——既有实现就是模板，agent 会照抄）
- API 清单（方法签名/参数——类型声明就是文档）
- 能从 git log/PRD/既有代码一眼确认的事实

## 操作

- **收录（ingest）**：按上述标准，每发现一个**代码说不清**的知识点写一页。链路类页面按"入口 → 要改的每一处 → 注意什么"组织，写明当下的代码位置。
  全部收录完跑 `seed wiki index --write`——生成 `index.md` + `log.md`，终端输出**涟漪候选**（新页面与已有页面的 token overlap 提示，辅助判断要不要补跨页引用）。

- **更新（update）**：对照当前代码逐条核对页面引用，修正失效的符号锚（`seed wiki lint` 会标出文件不存在/符号找不到的锚点）；代码已变而页面没变是 wiki 最大的失效模式。核实后将 `confidence` 重置为 `high` 并刷新 `last_updated`。更新后跑 `seed wiki index --write` 刷新索引和日志。

- **查询**：先看 `index.md` 扫类型→挑相关页；看 `log.md` 了解最近变更。精确检索用 `seed wiki search "<query>"` / `seed wiki collect --query "<query>" --limit 5 --json`。

- **体检**：`seed wiki lint --json`——断链、缺 frontmatter、孤儿页、行号 locator 漂移、低置信度页面过期提醒。

## 边界

- 用户触发 wiki skill 时做**集中收录、批量更新、体检**（ingest / update / lint）。
- brainstorm、impl、review 入场时各自加载 `seed wiki index --json` 暖场，收尾时按阶段职责写入——这些是各阶段的内部动作，不叫「触发 wiki skill」。
- 不收录代码本身能直接回答的事实（函数签名、单文件实现细节）；收录的是跨文件、易遗忘、有"为什么"的知识。
- 与 `.arbor/` 无依赖：wiki 跟项目走，不跟任务走。
