---
command: /breakdown
description: 任务分解
agent: TaskPlanner
---

# /breakdown

调用 **TaskPlanner**（任务规划师）进行任务分解。

## 用法

```bash
/breakdown <需求名>
/breakdown   # 如果在 /req-dev 流程中，自动获取
```

## 执行

1. 读取 `~/.claude/context/plans/<需求名>-plan.md`
2. 调用 **TaskPlanner** Agent
3. TaskPlanner 分解任务，每个 Task 拆 3-5 个小点
4. 产出 `~/.claude/context/tasks/<需求名>.tasks.md`
5. 询问："是否继续执行 /do？"
