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
/module-index app/Module/AiCreationCenter
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
├── AiCreationCenter-index.md
└── INDEX.md  # 总索引
```

## 执行流程

1. 分析模块目录结构
2. 识别关键类和方法
3. 分析依赖关系
4. 生成索引文件

## 索引内容格式

每个索引文件包含：

- **模块定位和职责**：模块的主要功能和定位
- **目录结构**：完整的目录树
- **关键类和方法摘要**：核心类、关键方法及其作用
- **依赖关系**：依赖的其他模块或外部库
- **入口点**：API 端点、路由、主要入口文件

示例：
```markdown
# User 模块索引

## 模块定位
负责用户注册、登录、个人信息管理等功能。

## 目录结构
```
app/Module/User/
├── Controller/
│   └── UserController.php
├── Service/
│   ├── UserService.php
│   └── AuthService.php
├── Model/
│   └── User.php
└── Repository/
    └── UserRepository.php
```

## 关键类和方法
- `UserController::login()` - 登录处理
- `UserService::register()` - 用户注册
- `AuthService::verifyToken()` - Token 验证

## 依赖关系
- 依赖 `Common/Database` 模块
- 使用 `Redis` 缓存用户会话

## 入口点
- POST /api/user/login
- POST /api/user/register
- GET /api/user/profile
```

## 自动更新

完成后自动更新 `./.claude/modules/INDEX.md`，添加新索引到总索引中。
