---
command: /extract-experience
description: 沉淀经验
agent: KnowledgeEngineer
---

# /extract-experience

调用 **KnowledgeEngineer**（知识工程师）沉淀经验。

## 用法

```bash
/extract-experience <名称>
```

## 执行步骤

KnowledgeEngineer 必须依次完成 3 个动作：

1. **生成经验文档** → `./.claude/experience/<名称>.md`
2. **更新 INDEX.md** → `./.claude/experience/INDEX.md`
3. **完成确认** → 输出两个文件路径

### 写入要求（保持精简）

- 先判断内容是否真的值得写成 experience；如果只是本次流水账，不要沉淀
- 如果只有一句高价值坑点，优先使用 `/remember`
- frontmatter 使用最小契约：`title/tags/files/updated/summary/kind/applies_when`
- `summary` 用一句话说明“什么时候该检索这条经验”
- `tags` 控制在 2–5 个高信号标签
- 不要为了完整而硬凑章节

## 完成后

```
✅ 经验文档已生成：./.claude/experience/<名称>.md
✅ 索引已更新：./.claude/experience/INDEX.md

发现规律？使用 /optimize-flow 沉淀为规则
```
