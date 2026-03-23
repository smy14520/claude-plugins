---
command: /module-index
description: 生成模块快速索引（项目目录）
---

# /module-index

为项目模块生成结构化索引，让 AI 快速理解模块而无需读取全部代码。

## 用法

```bash
/module-index <模块路径>
/module-index app/Module/User
/module-index <路径> --update  # 更新已有索引
```

## 路径说明

**索引存储在项目目录**：`./.claude/modules/`

```bash
# 在项目目录执行
/module-index app/Module/User

# 保存到
→ ./.claude/modules/User-index.md
```

## 输出目录结构

```
./.claude/modules/
├── User-index.md
├── Order-index.md
└── INDEX.md  # 总索引（纯索引，不含模块详情）
```

## 执行流程

1. 分析模块目录结构
2. 识别关键类和方法
3. 分析依赖关系
4. 生成索引文件
5. 更新 INDEX.md（追加/更新一行）

## 单个模块索引格式

每个模块索引文件（如 `User-index.md`）应该简洁精准：

```markdown
# User 模块

> 路径: `app/Module/User`
> 更新: 2026-02-11

## 职责
用户注册、登录、个人信息管理等功能。

## 目录结构
```
app/Module/User/
├── Controller/UserController.php
├── Service/
│   ├── UserService.php
│   └── AuthService.php
├── Model/User.php
└── Repository/UserRepository.php
```

## 关键入口

**API 端点**
- `POST /api/user/login` - 用户登录
- `POST /api/user/register` - 用户注册
- `GET /api/user/profile` - 获取个人信息

**核心类**
- `UserController` - 用户请求处理
- `UserService` - 用户业务逻辑
- `AuthService` - 认证服务

## 依赖
- `Common/Database` - 数据库访问
- `Redis` - 用户会话缓存
```

**原则**：
- 📌 **职责**：一句话说清楚模块做什么
- 📁 **目录结构**：简洁的树状图，只列主要文件
- 🔑 **关键入口**：API 端点和核心类，方便快速定位
- 🔗 **依赖**：列出外部依赖，不需要详细说明每个类的每个方法

## INDEX.md 格式

> ⚠️ **INDEX.md 是纯索引文件！** 只做"查找 → 定位"，不重复模块的具体内容。

```markdown
# 模块索引

> 最后更新: <日期>
> 模块总数: <数量>

| 模块 | 路径 | 索引文件 | 职责（一句话） | 更新时间 |
|------|------|----------|---------------|----------|
| User | app/Module/User | [User-index.md](./User-index.md) | 用户注册、登录、信息管理 | 2026-02-11 |
| Order | app/Module/Order | [Order-index.md](./Order-index.md) | 订单管理 | 2026-02-10 |
```

**INDEX.md 规则**：
- ✅ 只有一张表格 + 元信息
- ✅ "职责"列限制为一句话摘要（详细内容在各模块索引文件中）
- ❌ 不要往 INDEX.md 里塞功能说明、依赖关系图、技术栈分类、场景索引等
- 📌 需要了解模块详情？点击索引文件链接去看
