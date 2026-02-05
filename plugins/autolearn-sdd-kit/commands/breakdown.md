---
command: /breakdown
description: 在需求不清晰或任务复杂时，将其拆解为可执行的步骤。
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
6. **可选：同步到 Beads**（如果系统安装了 bd）
   - 检测命令：`which bd` 或 `where bd`（Windows）
   - 如果有输出，将 Markdown 任务同步到 Beads：
     ```bash
     # 为每个 Task 创建 Beads issue
     # 优先级规则：P0=阻塞其他任务，P1=正常，P2=可延后
     bd create "<Task标题>" --label <role> -p <优先级>
     # 设置依赖关系（如果有）
     bd dep add <子任务ID> <父任务ID>
     ```
   - **将 Beads ID 记录到 Markdown**：在每个 Task 中添加 `**beads_id**` 字段
     ```markdown
     ## Task 1: 实现登录页面 ⏳
     **role**: frontend
     **stack**: React, TypeScript
     **beads_id**: bd-abc123  ← 新增此行（与 role/stack 格式一致）

     - [ ] 1.1 创建 Login 组件
     - [ ] 1.2 实现表单验证
     ```
7. ⏸️ **必须暂停等待确认**（禁止自动继续）

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
