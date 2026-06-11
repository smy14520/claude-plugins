---
name: research
description: "为一个需求收集外部资料、竞品/API/字段/流程信息，并整理成 .sdd/research/<topic>/ 资料包。只做资料探索，不做最终 PRD 或方案决策。"
---

# Research — 外部资料包

Research 的职责是收集和整理资料，让后续 brainstorm 有足够上下文。它不是方案设计器，不写 PRD，不自动进入下一阶段。

## 使用场景

- 用户要做一个新产品，需要先看竞品、数据源、行业资料。
- 用户要接入外部平台，需要先收集 API、鉴权、回调、字段、限制。
- 用户给了 URL / 文档 / 竞品，希望整理成 AI 可读资料。
- 用户明确说“先调研”“收集资料”“看看别人怎么做”。

## 不使用场景

- 用户已经要明确收敛需求：用 brainstorm。
- 用户要求直接实现：用 impl，但 impl 应确认是否已有 PRD。
- 用户要求长期记录项目知识：用 wiki。
- 单一事实问答不需要建立 research workspace。

## 产物

```text
.sdd/research/<topic>/
├── index.md      # 资料包入口：目标、当前理解、来源导航、缺口、readiness
├── summary.md    # 给 brainstorm 的压缩摘要
├── sources/      # 原文摘录或 source-backed notes
└── notes/        # 主题化整理：这对需求意味着什么
```

## Hard rules

1. 用户提供的 URL / 文档 / 明确来源必须尝试获取；无法获取时记录失败原因。
2. `sources/` 只保存来源事实，不写最终产品决策。
3. `notes/` 可以解释“这对需求意味着什么”，但不能拍板最终 scope。
4. `summary.md` 是给 brainstorm 的阅读入口，不是 PRD。
5. 不自动写 wiki；只有用户显式要求“收录到 wiki”才交给 wiki。
6. 不自动进入 brainstorm；research 最多建议“资料已足够进入 brainstorm”。
7. 不捏造不可获取来源的内容。

## Workflow

### 1. Frame

先明确 research question：

- 用户真正想了解什么？
- 下游是 brainstorm、直接回答，还是 wiki source 归档？
- 成功标准是什么？比如“知道竞品功能结构”“知道 API 接入流程”“知道可抓取字段”。

如果意图不清，先问一个最高价值问题。

### 2. Collect

按来源收集：

- 用户给的 URL / 文档。
- 竞品页面。
- API 文档。
- 开发者平台限制。
- 字段 / 数据结构 / 回调格式。
- 需要登录或人工确认的资料。

每个 source 文件必须包含来源、获取时间、内容摘要和原文摘录。

### 3. Note

把 sources 整理成主题笔记。每篇 note 至少回答：

- 当前结论是什么？
- 来源是什么？
- 这对需求意味着什么？
- 仍然缺什么？

### 4. Snapshot

更新 `index.md` 和 `summary.md`。

`summary.md` 面向 brainstorm，应包含：

- 最重要结论。
- 可用事实。
- 未确认风险。
- 推荐在 brainstorm 中决策的问题。
- 关键 source 路径。

## Readiness

Research 的状态只需要三种：

```text
open   仍在收集
ready  足够交给 brainstorm
closed 用户认为本轮结束
```

`ready` 不代表需求已经明确，只代表资料足够进入 brainstorm。
