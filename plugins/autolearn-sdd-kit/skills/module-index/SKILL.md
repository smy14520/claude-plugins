---
name: module-index
description: 生成模块快速索引（项目目录）
triggers: [/module-index]
---

# module-index

为项目模块生成结构化索引，让 AI 快速理解模块而无需读取全部代码。

## 路径说明

**索引存储在项目目录**：`.claude/context/modules/`

```bash
# 在项目目录执行
/module-index app/Module/User

# 保存到
→ .claude/context/modules/User-index.md
```

## 命令

```bash
/module-index <模块路径>
/module-index app/Module/AiCreationCenter
/module-index <路径> --update  # 更新已有索引
```

## 输出目录结构

```
.claude/context/modules/
├── User-index.md
├── Order-index.md
└── AiCreationCenter-index.md
```

## 索引内容

- 模块定位和职责
- 目录结构
- 关键类和方法摘要
- 依赖关系
- 入口点

## 自动更新

完成后自动更新 `.claude/context/modules/INDEX.md`

## 如何被使用

当执行 `/req-dev` 或 `/detect-context` 时：
1. `detect-context` 识别当前项目
2. 查看 `.claude/context/modules/` 下有哪些索引
3. 根据需求关键词匹配模块名
4. 自动加载匹配的模块索引

示例：
```
需求: "修改 User 模块的登录逻辑"
        ↓
匹配: .claude/context/modules/User-index.md
        ↓
AI 获得 User 模块结构，直接定位关键代码
```
