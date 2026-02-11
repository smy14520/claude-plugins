---
description: 生成模块快速索引
agent: knowledge-engineer
subtask: true
---

为项目模块生成结构化索引，让 AI 快速理解模块而无需读取全部代码。

## 用法

```
/module-index <模块路径>
/module-index <模块路径> --update  # 更新已有索引
```

等价于：`$1` 为模块路径。

## 路径说明

**索引存储在项目目录**：`./.claude/modules/`（与 Claude Code 共享）

```
/module-index app/Module/User
→ ./.claude/modules/User-index.md
```

## 执行流程

1. 分析 `$1` 对应的模块目录结构
2. 识别关键类和方法
3. 分析依赖关系
4. 生成索引文件到 `./.claude/modules/`
5. 更新 `./.claude/modules/INDEX.md`

## 单个模块索引格式

```markdown
# <模块名> 模块

> 路径: `<模块路径>`
> 更新: <日期>

## 职责
一句话说清楚模块做什么。

## 目录结构
（简洁树状图，只列主要文件）

## 关键入口
**API 端点**
- `POST /api/xxx` - 描述

**核心类**
- `XxxController` - 描述
- `XxxService` - 描述

## 依赖
- `Common/Database` - 数据库访问
```

## INDEX.md 格式

**INDEX.md 是纯索引文件，只包含数据，不包含使用说明。**

```markdown
# 模块索引

> 最后更新: <日期>
> 模块总数: <数量>

## 📋 索引列表

| 模块 | 路径 | 索引文件 | 更新时间 | 职责 | 标签 |
|------|------|----------|----------|------|------|
| User | app/Module/User | [User-index.md](./User-index.md) | 2026-02-11 | 用户管理 | `auth`, `backend` |

## 🏗️ 模块依赖关系

（用 Mermaid 图展示模块依赖关系）

## 🔍 按技术栈索引
## 🏷️ 按标签索引
## 📦 按业务域分类
## 🔗 常见场景快速索引
```
