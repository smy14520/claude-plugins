---
name: extract-experience
description: 沉淀经验
argument-hint: "[名称]"
allowed-tools: "Read, Write, Edit, Glob, Grep, Task"
model: sonnet
---

# /autolearn-sdd-kit:extract-experience

调用 **KnowledgeEngineer**（知识工程师）沉淀经验。

## 用法

```bash
/autolearn-sdd-kit:extract-experience <名称>
```

## 执行步骤

这是一个薄 orchestrator 命令：
- 最小必要上下文
- 一次委派给 `KnowledgeEngineer`
- 结果足够时立即落盘
- 不输出“如果你愿意我下一步可以……”这类闲聊收尾

KnowledgeEngineer 必须依次完成 3 个动作：

1. **生成经验文档** → `./.claude/experience/<名称>.md`
2. **更新 INDEX.md** → `./.claude/experience/INDEX.md`
3. **完成确认** → 只输出两个文件路径

### 写入要求（保持精简）

- 先判断内容是否真的值得写成 experience；如果只是本次流水账，不要沉淀
- 如果只有一句高价值坑点，优先使用 `/autolearn-sdd-kit:remember`
- frontmatter 使用最小契约：`title/tags/files/updated/summary/kind/applies_when`
- `summary` 用一句话说明“什么时候该检索这条经验”
- `tags` 控制在 2–5 个高信号标签
- 不要为了完整而硬凑章节

## 完成后

```
✅ 经验文档已生成：./.claude/experience/<名称>.md
✅ 索引已更新：./.claude/experience/INDEX.md
```
