---
command: /design
description: 方案设计
agent: Architect
---

# /design

调用 **Architect**（架构师）进行方案设计。

## 用法

```bash
/design <需求描述>
/design   # 如果在 /req-dev 流程中，自动获取需求
```

## 执行

1. 调用 **Architect** Agent
2. Architect 设计 Spec & Plan
3. 产出 `~/.claude/context/plans/<需求名>-plan.md`
4. 询问："是否继续执行 /breakdown？"
