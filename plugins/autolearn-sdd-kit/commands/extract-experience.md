---
command: /extract-experience
description: 在完成任务后，总结并沉淀可复用的规则或流程。
agent: KnowledgeEngineer
---

# /extract-experience

调用 **KnowledgeEngineer**（知识工程师）沉淀经验。

## 用法

```bash
/extract-experience <名称>
/extract-experience <名称> --common   # 沉淀为通用经验
```

## 执行

1. 调用 **KnowledgeEngineer** Agent
2. KnowledgeEngineer 提取关键信息
3. 产出 `.claude/context/experience/<名称>.md`
4. 更新 `.claude/context/experience/INDEX.md`
5. 询问："发现规律？使用 /optimize-flow 沉淀为规则"
