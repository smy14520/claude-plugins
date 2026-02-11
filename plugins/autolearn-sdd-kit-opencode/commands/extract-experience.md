---
description: 沉淀经验
agent: knowledge-engineer
subtask: true
---

调用 **knowledge-engineer** 沉淀经验。

## 用法

```
/extract-experience <名称>
/extract-experience <名称> --common   # 沉淀为通用经验
```

等价于：`$ARGUMENTS` 为名称。

## 执行

1. 调用 **knowledge-engineer** subagent
2. 提取关键信息（核心文件、流程、坑点）
3. 产出 `./.claude/experience/$ARGUMENTS.md`
4. 更新 `./.claude/experience/INDEX.md`
5. 询问："发现规律？使用 /optimize-flow 沉淀为规则"
