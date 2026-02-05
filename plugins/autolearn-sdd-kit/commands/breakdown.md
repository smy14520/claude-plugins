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

## 前置条件

- `.claude/context/plans/<需求名>-plan.md` 的 `review_status` 必须为 `approved`

## 执行

1. 检查设计方案是否已确认
2. 读取 `.claude/context/plans/<需求名>-plan.md`
3. 调用 **TaskPlanner** Agent
4. TaskPlanner 分解任务，每个 Task：
   - 标注 `role`（frontend / backend / mobile / devops）
   - 标注 `stack`（技术栈）
   - 拆分 3-5 个可执行小点
5. 产出 `.claude/context/tasks/<需求名>.tasks.md`
   - 文件头包含 `review_status: pending`
   - 文件头包含 `confirm_each: false`
6. ⏸️ **必须暂停等待确认**（禁止自动继续）

## 确认流程

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 任务清单已完成，请审阅

共 X 个 Task，涉及角色：frontend, backend

您可以：
- 输入 "确认" 或 "ok" → 继续下一步（/do）
- 输入 "修改: <意见>" → 修改清单后重新审阅
- 输入 "重做" → 从头重新分解
- 输入 "逐步确认" → 设置 confirm_each: true 后继续
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

确认后：
1. 更新 `review_status: approved`
2. 继续执行 `/do`
