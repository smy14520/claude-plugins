---
command: /impl
description: 执行实现
agent: Developer
---

# /impl

调用 **Developer** 执行任务实现。

## 用法

```bash
/impl <需求名>
```

## 执行

1. 读取 `./.claude/tasks/<需求名>.tasks.md`
2. 调用 **Developer** Agent
3. 按 Task 顺序执行：
   - 读取 `role` 和 `stack` 标签
   - 根据技术栈调整实现策略
   - 执行该 Task 的所有小点
   - 更新 checkbox 状态
4. 全部完成后提醒 `/extract-experience`

## 执行示例

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 开发任务已完成

需求: GitHub-SSO登录

完成清单:
✅ Task 1: 实现登录页面 (frontend)
✅ Task 2: 实现 OAuth 后端 (backend)

修改文件:
- src/components/Login.tsx
- src/pages/login.tsx
- server/routes/auth.ts
- server/services/oauth.ts

下一步: /extract-experience GitHub-SSO登录
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**完成后必须立即返回，不要挂起等待。**
