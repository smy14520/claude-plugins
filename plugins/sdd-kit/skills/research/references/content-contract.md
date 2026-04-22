# Research 文件内容契约

Research 文件夹中的每个文件共同组成一个**index-first、可增量更新的需求探索工作区**。

## 逐文件契约

| 文件 | 包含 | 不包含 |
|------|------|--------|
| `index.md` | 当前研究问题 / 当前理解 / 范围 / 主题导航 / 关键来源 / open questions / readiness | 完整原始摘录、最终设计决策 |
| `log.md` | 研究过程中的追加式记录：本轮做了什么、理解怎么变了 | 长篇总结、完整原始证据 |
| `raw/*.md` | 带来源引用的原文摘录 | 解读、抽象、决策 |
| `notes/*.md` | 每文件一个主题；带来源的解释、含义、未决问题 | 最终设计决策、多主题混合 |

## index.md 契约

frontmatter：
- `status: open | ready-for-brainstorm | closed`
- `topic: <topic-kebab-case>`
- `updated: YYYY-MM-DD`
- `downstream: <brainstorm-name | direct-answer | wiki-ingest>`

必需章节：
- `## 研究问题`
- `## 当前理解`
- `## 当前范围 / 暂不纳入`
- `## 意图锚定`
- `## 主题导航`
- `## 关键来源`
- `## 仍未解决的问题`
- `## 当前是否适合进入 brainstorm`
- `## 下一步（用户决定）`

## log.md 契约

记录理解如何变化，是时间轴，不是主页。

## raw/ 契约

每个文件是按来源界定的摘录缓存。raw 不写解读或决策。

## notes/ 契约

每个文件是一个主题化研究笔记，至少包含：
- 当前结论
- 来源
- 这对需求意味着什么
- 仍未解决的问题
- 相关笔记

## research 与 brainstorm / wiki 的关系

- `research` 负责发散 → 收敛：把需求理解推进到足够清晰
- `brainstorm` 负责收敛 → 形成可拆解的 PRD/context artifact
- `wiki` 负责长期沉淀：仅将真正跨需求可复用的内容提升进去
