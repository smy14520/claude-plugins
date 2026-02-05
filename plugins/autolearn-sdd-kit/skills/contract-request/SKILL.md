---
name: contract-request
description: 跨角色协作机制，前后端通过 Contract Request 同步接口需求
---

# Contract Request

## 使用场景

开发过程中发现后端接口不满足需求：
- 缺少必要字段
- 字段类型不匹配
- 需要新的 API 端点

## Beads 模式

### 创建 Contract Request

```bash
# 1. 创建 Contract Request
bd create "添加 <字段名> 字段到 <接口>" \
  --label backend,contract \
  -p 0 \
  --desc "用于 <用途说明>，示例: {示例payload}"

# 2. 将当前任务标记为 blocked
bd dep add <当前任务ID> <contractRequestID>
```

**示例**：
```bash
bd create "添加 avatar 字段到 /api/user" \
  --label backend,contract \
  -p 0 \
  --desc "用于用户列表展示头像，示例: {id: 1, name: 'xxx', avatar: 'https://...'}"

bd dep add bd-frontend-123 bd-contract-456
```

### Contract Request 描述模板

```markdown
## Contract Request

### API 端点
GET /api/user

### 缺失字段
- **字段名**: avatar
- **类型**: string (URL)
- **说明**: 用户头像 URL

### 用途
用户列表页面展示用户头像

### 示例 payload
{
  "id": 1,
  "name": "张三",
  "avatar": "https://cdn.example.com/avatar/1.jpg"
}

### 优先级
P0 - 阻塞前端开发

### 创建者
FrontendDeveloper - <当前任务ID>
```

### 等待后端处理

- 当前任务自动进入 blocked 状态
- 后端会在 `bd ready --label backend` 中看到 contract
- 后端完成后，当前任务自动解除阻塞

### 处理 Contract Request（BackendDeveloper）

```bash
# 获取后端任务时，contract 会优先出现
bd ready --label backend
# 输出示例：
# bd-contract-123  [contract] 添加 avatar 字段到 /api/user  (P0)
# bd-abc-456       实现 /api/order 创建接口            (P1)
```

**处理流程**：
1. 分析需求（接口、缺失字段、用途）
2. 数据库设计（添加字段、索引）
3. 实现接口（修改查询、更新类型）
4. 更新契约文件（docs/contracts）
5. 完成 Contract：`bd close bd-contract-123`

### 契约文件模板

更新 `docs/contracts/<接口名>.md`：

```markdown
# GET /api/user

## 描述
获取用户信息

## 请求
- Method: GET
- Path: /api/user/:id

## 响应
{
  "id": 1,
  "name": "张三",
  "email": "zhang@example.com",
  "avatar": "https://cdn.example.com/avatar/1.jpg",
  "createdAt": "2024-01-01T00:00:00Z"
}

## 字段说明
| 字段 | 类型 | 说明 |
|------|------|------|
| id | number | 用户 ID |
| name | string | 用户名 |
| email | string | 邮箱 |
| avatar | string | 头像 URL（新增） |
| createdAt | string | 创建时间 |

## 更新记录
- 2024-01-15: 添加 avatar 字段（Contract #bd-contract-123）
```

## Markdown 模式

### 创建 Contract Request（FrontendDeveloper）

在当前任务的 Markdown 中添加：

```markdown
## Task 1: 实现用户列表 ⏸️  ← 修改标记为暂停
**role**: frontend
**stack**: React, TypeScript

## Contract Request

### API 端点
GET /api/user

### 缺失字段
- [ ] 添加 avatar 字段
  - **类型**: string (URL)
  - **说明**: 用户头像 URL
  - **用途**: 用户列表页面展示头像
  - **示例**: {"avatar": "https://cdn.example.com/avatar/1.jpg"}
  - **优先级**: P0（阻塞当前任务）

### 创建者
FrontendDeveloper - Task 1

---

- [ ] 1.1 创建用户列表组件
- [ ] 1.2 实现 avatar 字段展示  ← 等待 Contract 完成后继续
```

### 处理 Contract Request（BackendDeveloper）

```markdown
## 检查 Contract Request

1. 搜索所有前端任务中的 `## Contract Request` 部分
2. 找到 Task 标题中带有 `⏸️` 标记的任务（表示被阻塞）
3. 优先处理 Contract Request 中的缺失字段
4. 处理完成后：
   - 将 Contract Request 中的 `- [ ]` 改为 `- [x]`（标记字段已添加）
   - 将 Task 标题的 `⏸️` 改回 `⏳`（解除阻塞）
   - 在 Contract Request 末尾添加处理记录：
     ```markdown
     ### 处理记录
     - 2024-01-15: BackendDeveloper 添加 avatar 字段，完成 Contract
     ```
```

**示例**：

```markdown
## Task 1: 实现用户列表 ⏸️  ← 处理后改为 ⏳
**role**: frontend

## Contract Request
...
- [x] 添加 avatar 字段  ← 打勾

### 处理记录
- 2024-01-15: BackendDeveloper 添加 avatar 字段到 users 表
```

## 流程总结

```
前端发现接口问题
    ↓
创建 Contract Request（Beads 或 Markdown）
    ↓
前端任务 blocked/⏸️
    ↓
后端发现并处理 Contract
    ↓
更新契约文件
    ↓
完成 Contract（bd close 或改 ⏸️ 为 ⏳）
    ↓
前端任务解除阻塞，继续执行
```

## 优势

| 优势 | 说明 |
|------|------|
| **有记录** | 每个 Contract 都是永久记录 |
| **可追溯** | 完整的历史和处理记录 |
| **不靠记忆** | 不依赖聊天记录 |
| **顺序保证** | 依赖机制自动保证执行顺序 |
| **优先级** | label 让后端优先看到 contract |
