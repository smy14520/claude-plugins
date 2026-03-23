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

## 完成后

```
✅ 经验文档已生成：./.claude/experience/<名称>.md
✅ 索引已更新：./.claude/experience/INDEX.md

发现规律？使用 /optimize-flow 沉淀为规则
```
