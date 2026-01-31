# Commands

命令是**用户交互的入口**，用动词命名，调用对应的 Agent 执行。

## 命令列表

| 命令 | 用途 | 调用的 Agent |
|------|------|--------------|
| [/req-dev](req-dev.md) | SDD 流程编排 | 编排多个 Agent |
| [/design](design.md) | 方案设计 | Architect |
| [/breakdown](breakdown.md) | 任务分解 | TaskPlanner |
| [/do](do.md) | 执行实现 | Developer |
| [/extract-experience](extract-experience.md) | 沉淀经验 | KnowledgeEngineer |
| [/optimize-flow](optimize-flow.md) | 沉淀规则 | KnowledgeEngineer |
| [/remember](remember.md) | 即时记录 | - |
| [/module-index](module-index.md) | 模块索引 | - |

## 设计原则

1. **命令是动词**：`/design`、`/do`、`/breakdown`
2. **Agent 是角色**：`Architect`、`Developer`、`TaskPlanner`
3. **命令调用 Agent**：命令负责触发，Agent 负责执行
