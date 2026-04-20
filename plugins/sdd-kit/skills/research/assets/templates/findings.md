---
status: open | closed
date: YYYY-MM-DD
topic: <topic-kebab-case>
---

<!-- 输出语言: 中文 -->

# 研究: <topic>

## 研究问题

<从 question.md 复制 — 一句话>

## 核心发现

- **<发现 1 标题>** — <一句话摘要> → `refined/<note-1>.md`
- **<发现 2 标题>** — <一句话摘要> → `refined/<note-2>.md`
- **<发现 3 标题>** — <一句话摘要> → `refined/<note-3>.md`

## 待解决问题

（需要在 spec 阶段解决的 — 明确列出。如果确实没有，请说明并解释确认方式。）

- <待解决问题 1>
- <待解决问题 2>

## 入库候选

（值得提升为长期 wiki 知识的精炼笔记。用户需显式执行 `wiki` 入库操作。）

- `refined/<note-a>.md` → 建议 wiki 类型: `entity` / 名称: `<wiki-page-name>`
- `refined/<note-b>.md` → 建议 wiki 类型: `gotcha` / 名称: `<wiki-page-name>`
- `refined/<note-c>.md` → 建议 wiki 类型: `concept` / 名称: `<wiki-page-name>`

## 临时性内容（不要入库）

（仅限当前决策范围的精炼笔记，无复用价值。）

- `refined/<note-x>.md` — 仅与本次决策相关
- `refined/<note-y>.md` — 在范围内已被 `<note-a>` 取代

## 后续步骤（由用户决定，不自动触发）

- 运行 `spec` 技能起草设计（待解决问题将变为决策点）
- 运行 `wiki` 入库提升候选笔记
- 或暂不操作，后续再议
