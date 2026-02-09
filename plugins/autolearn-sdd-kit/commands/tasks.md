---
command: /tasks
description: 任务规划
agent: TaskPlanner
---

# /tasks

调用 **TaskPlanner**（任务规划师）进行任务分解。

## 用法

```bash
/tasks <需求名>
```

## 执行

1. 读取 `./.claude/plans/<需求名>-plan.md` 设计方案
2. 调用 **TaskPlanner** Agent
3. 分解任务，每个 Task：
   - 标注 `role`（frontend / backend / mobile / devops）
   - 标注 `stack`（技术栈）
   - 拆分 3-5 个可执行小点
4. 产出 `./.claude/tasks/<需求名>.tasks.md`

## 完成后

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 任务规划已完成

共 X 个 Task，涉及角色：frontend, backend

文件: ./.claude/tasks/<需求名>.tasks.md

下一步: /impl <需求名>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
