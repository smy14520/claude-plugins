---
command: /design
description: 调用架构师进行方案设计
agent: Architect
---

# /design

调用 **Architect** 进行方案设计。

## 用法

```bash
/design <需求描述>
```

## 执行

1. 调用 **Architect** Agent
2. Architect 分析项目上下文
3. 通过渐进式访谈理解需求
4. 提出 2-3 个方案对比
5. 分段呈现设计，逐段确认
6. 产出 `./.claude/plans/<需求名>-plan.md`

## 完成后

```
✅ 设计方案已完成
文件: ./.claude/plans/<需求名>-plan.md

下一步: /tasks <需求名>
```
