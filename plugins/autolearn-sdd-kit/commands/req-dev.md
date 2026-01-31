---
command: /req-dev
description: SDD 规范驱动开发流程编排
---

# /req-dev

SDD 规范驱动开发的**流程编排命令**，负责意图识别和 Agent 调度。

## 用法

```bash
/req-dev                      # 查看进行中的需求
/req-dev <需求描述>            # 开始新需求
/req-dev 继续 <需求名>         # 断点续做
```

## 流程编排

```
/req-dev <需求描述>
    │
    ├─ 1. 意图识别
    │      判断：新需求 / 继续 / 修bug / 查询
    │
    ├─ 2. 调用 ContextDetective
    │      检索规则、经验、模块索引
    │      输出上下文报告
    │
    ├─ 3. 调用 Architect
    │      设计 Spec & Plan
    │      产出: plans/<需求名>-plan.md
    │
    ├─ 4. 调用 TaskPlanner
    │      分解任务清单
    │      产出: tasks/<需求名>.tasks.md
    │
    ├─ 5. 调用 Developer
    │      逐个执行任务
    │      产出: 代码
    │
    └─ 6. 调用 KnowledgeEngineer（/extract-experience）
           沉淀经验
           产出: experience/<project>/<名称>.md
```

## 意图识别

| 输入 | 意图 | 执行 |
|------|------|------|
| 无参数 | 查看需求 | 列出进行中的 tasks 文件 |
| `继续 xxx` | 断点续做 | 读取 tasks 文件，从未完成处继续 |
| 含 "修复/bug" | fix_bug | 跳过 design/breakdown，直接 do |
| 其他 | 新需求 | 完整流程 |

## 断点续做

```bash
/req-dev 继续 GitHub-SSO登录
```

1. 读取 `~/.claude/context/tasks/GitHub-SSO登录.tasks.md`
2. 找到第一个 `- [ ]` 的小点
3. 调用 Developer 从该小点继续
