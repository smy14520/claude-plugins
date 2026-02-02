---
command: /do
description: 执行实现
agent: Developer
---

# /do

调用 **Developer**（开发统筹）执行任务。

## 用法

```bash
/do <需求名>
/do   # 如果在 /req-dev 流程中，自动获取
```

## 前置条件

- `tasks/<需求名>.tasks.md` 的 `review_status` 必须为 `approved`

## 执行

1. 检查任务清单是否已确认
2. 读取 `~/.claude/context/tasks/<需求名>.tasks.md`
3. 调用 **Developer** Agent（开发统筹）
4. Developer 根据 Task 的 `role` 调度专业开发者：
   - `frontend` → FrontendDeveloper
   - `backend` → BackendDeveloper
   - `mobile` → MobileDeveloper
   - `devops` → DevOpsDeveloper
5. 执行所有小点，完成后标记 `- [x]`
6. 全部完成后提醒 `/extract-experience`

## 执行模式

### 默认模式（连续执行）

连续执行所有任务，不中断。

### 逐步确认模式

触发条件：
- 用户说"逐步确认"
- tasks 文件设置 `confirm_each: true`

每个 Task 完成后暂停，等待确认。

## 执行示例

```
【Developer 执行中】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

需求: GitHub-SSO登录

✅ Task 1: 实现登录页面 (frontend)
   → 调度 FrontendDeveloper
   ✓ 1.1 创建 Login 组件
   ✓ 1.2 实现表单验证

✅ Task 2: 实现 OAuth 后端 (backend)
   → 调度 BackendDeveloper
   ✓ 2.1 创建 /auth/github 路由
   ✓ 2.2 实现 token 交换

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
全部完成！建议执行 /extract-experience
```

