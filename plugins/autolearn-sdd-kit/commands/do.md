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

- `.claude/context/tasks/<需求名>.tasks.md` 的 `review_status` 必须为 `approved`

## 执行

1. 检查任务清单是否已确认
2. 读取 `.claude/context/tasks/<需求名>.tasks.md`
3. **检测环境**：检查是否安装了 Beads
   ```bash
   which bd
   ```
4. 调用 **Developer** Agent（开发统筹），传递环境信息
5. Developer 根据环境和 Task 的 `role` 调度专业开发者：
   - `frontend` → FrontendDeveloper
   - `backend` → BackendDeveloper
   - `mobile` → MobileDeveloper
   - `devops` → DevOpsDeveloper
6. 执行所有小点，完成后标记 `- [x]`
7. 全部完成后提醒 `/extract-experience`

## 执行模式

### 默认模式（连续执行）

连续执行所有任务，不中断。

### 逐步确认模式

触发条件：
- 用户说"逐步确认"
- tasks 文件设置 `confirm_each: true`

每个 Task 完成后暂停，等待确认。

## 执行示例

### Beads 并发模式

```
【Developer 执行中 - Beads 模式】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

需求: GitHub-SSO登录

检测到 Beads，启用并发执行...

FrontendDeveloper (并行):
✅ Task 1: 实现登录页面
   → bd claim bd-abc1 ✓
   → 发现接口缺字段，创建 Contract Request: bd-contract-999
   → 当前任务 blocked，等待后端...

BackendDeveloper (并行):
✅ Task 2: 实现 OAuth 后端
   → bd claim bd-def1 ✓
   ✓ 2.1 创建 /auth/github 路由
   ✓ 2.2 实现 token 交换

✅ Contract Request: 添加 avatar 字段
   → bd claim bd-contract-999 ✓
   → 添加字段到数据库
   → 更新 docs/contracts
   → bd close bd-contract-999

FrontendDeveloper (继续):
✅ Task 1: 实现登录页面
   → 依赖完成，自动解除阻塞
   ✓ 1.1 创建 Login 组件
   ✓ 1.2 实现表单验证
   ✓ 1.3 接入 avatar 字段

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
全部完成！建议执行 /extract-experience
```

### Markdown 串行模式

```
【Developer 执行中 - Markdown 模式】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

需求: GitHub-SSO登录
模式: Markdown（未安装 Beads）

✅ Task 1: 实现登录页面 (frontend)
   → 调度 FrontendDeveloper
   ✓ 1.1 创建 Login 组件
   ✓ 1.2 实现表单验证
   ✓ 1.3 接入 OAuth 跳转

✅ Task 2: 实现 OAuth 后端 (backend)
   → 调度 BackendDeveloper
   ✓ 2.1 创建 /auth/github 路由
   ✓ 2.2 实现 token 交换

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
全部完成！建议执行 /extract-experience
```

