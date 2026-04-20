# Research 文件内容契约

Research 文件夹中的每个文件都有明确的目的。混淆它们是主要的失败模式。

## 逐文件契约

| 文件 | 包含 | 不包含 |
|------|------|--------|
| `question.md` | 范围 / 排除范围 / 喂养决策 | 发现、原始摘录、决策 |
| `raw/*.md` | 带来源引用的原文摘录 | 解读、抽象、决策 |
| `refined/*.md` | 每文件一个原子发现 | 多个发现、决策、任务 |
| `findings.md` | 摘要 + 未决问题 + 摄取候选 | 完整发现细节（链接至 refined/） |

## question.md 契约

目的：冻结范围，使研究保持有界。

必需的章节：

- `# Question` — 一句话
- `## In scope` — 2-4 个具体子问题
- `## Out of scope` — 至少 2 个明确排除项
- `## Feeding decision` — 哪个 spec/task 将消费此研究
- `## Time budget`（可选）— 粗略的小时/天数估算

禁止包含：

- 发现（尚未发现任何内容）
- 试探性意见（"我认为我们应该……"）
- 对 wiki 页面的引用（question 处于研究之前）

## raw/ 契约

每个文件是一个按来源界定的摘录缓存。

必需的章节：

- `# <标题>`
- `> Source: <URL | path | user>` 引用块
- `> Collected: YYYY-MM-DD`
- `## Content` — 原文或近乎原文的摘录

禁止包含：

- 解读（"这意味着 X"）— 属于 `refined/`
- 决策（"所以我们应该做 Y"）— 属于 spec
- 风格改写 — raw 就是 raw

### raw 上允许的变换

- 截断（删除不相关段落，注明删除了什么）
- 翻译（如果来源是其他语言），附带注释 "Translated from <lang>"
- 格式归一化（HTML → markdown）

### 不允许的操作

- 导致失真的概括
- 将多个来源合并到一个 raw 文件（一个来源一个文件）
- 剥离引用或行号

## refined/ 契约

每个文件是**一个原子发现**。如果你无法用单个具体主题命名文件，说明你在混合发现——拆分。

必需的章节：

- `# <发现标题>`
- `## What I found` — 1-3 句话
- `## Where` — 引用回 `raw/` 文件并附带行号参考
- `## Why it matters` — 与喂养决策的关联
- `## Open question` — 仍然未知的内容（可以明确写"无"）

禁止包含：

- 一个文件中包含多个不同发现
- 无引用来源的断言（"我注意到"但没有 `raw/` 引用）
- 决策或建议

### 硬性限制

- 每条笔记不超过 80 行
- 至少一个 `raw/` 引用；如果无法引用，则该发现是推测性的——移至"未决问题"或丢弃

### 可选 frontmatter

```yaml
---
finding-type: landscape | gotcha | constraint | precedent
confidence: low | medium | high
---
```

## findings.md 契约

目的：spec 作者阅读的单文件摘要，用于了解此次研究产生了什么。

必需的章节：

- `# Research: <topic>`
- 包含 `status: open | closed`、`date` 的 frontmatter
- `## Question` — 从 question.md 复制
- `## Key findings` — 不超过 7 个要点，每个以 wikilink 样式引用一条提炼笔记
- `## Open questions` — 要点列表，供 spec 解决
- `## Ingest candidates` — 值得提升至 wiki 的提炼笔记，每个标注建议类型
- `## Ephemeral` — 明确不用于 wiki 的提炼笔记（仅限本次决策范围）

禁止包含：

- 发现的完整细节（链接至 refined/ 代替；findings.md 是目录，不是内容本身）
- 决策（"我们选择了 X"）— 决策存在于 spec 中
- 自动 wiki 摄取的副作用（findings.md 仅*提议*）

### "独立可读"测试

`findings.md` 应该对没有读过 `raw/` 或 `refined/` 的 spec 作者可读。如果他们需要阅读详细文件才能理解摘要，说明摘要写得不够充分。

## spec 撰写之后研究怎么处理？

Research 文件夹在 spec 定稿后**不会被删除**。它们作为历史记录保留。

可选：在 `findings.md` 的 frontmatter 中标记 `status: consumed-by-spec: <spec-name>`，让后续会话知道此研究已被消费。

## 跨多次研究的共享发现怎么办？

如果 research-A 中的发现 X 也适用于 research-B：

- 从两个研究的 `findings.md` 中链接到该提炼笔记
- 如果发现 X 确实可复用，它就是一个**摄取候选** — 提升至 wiki，然后两个研究都可以链接到 `[[wiki-page]]` 而非原始提炼笔记
