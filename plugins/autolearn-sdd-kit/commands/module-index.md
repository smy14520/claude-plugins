---
command: /module-index
description: 生成模块索引
---

# /module-index

为项目模块生成结构索引，加速后续开发。

## 用法

```bash
/module-index <模块路径>
/module-index app/Module/User
```

## 执行

1. 分析模块结构
2. 产出 `./.claude/modules/<模块名>-index.md`

## 索引内容

- 模块定位和职责
- 目录结构
- 关键类和方法
- 入口点
- 依赖关系
