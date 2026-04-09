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
3. 使用 TaskCreate 注册所有 Task 到系统
4. 按 Task 顺序执行，TaskUpdate 追踪进度
5. 如果 Task 标注了 `depends_on: []` 且用户要求并行，可用 Agent 工具派发 subagent
6. 执行时以 tasks 文件为准，不要自行补充未被任务或验收标准要求的功能性复杂度
7. 全部完成后提醒 `/extract-experience`

## 用户指令优先

用户可以在任何时候用自然语言控制行为：
- "不写测试" → 跳过测试
- "要写测试" → 强制写测试
- "并行实现" → 无依赖 Task 并行执行
- "这个 Task 跳过" → 跳过指定 Task
- CLAUDE.md 中的配置优先级最高

**完成后必须立即返回，不要挂起等待。**
