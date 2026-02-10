# Agents

Agent 是**拟人化的角色**，具有明确的身份和职责。

## Agent 列表

| Agent | 身份 | 职责 |
|-------|------|------|
| [Architect](Architect.md) | 架构师 | 设计 Spec & Plan |
| [TaskPlanner](TaskPlanner.md) | 任务规划师 | 分解任务、制定清单 |
| [Developer](Developer.md) | 开发统筹 | 按 role/stack 执行实现 |
| [KnowledgeEngineer](KnowledgeEngineer.md) | 知识工程师 | 沉淀经验、提炼规则 |
| [ContextDetective](ContextDetective.md) | 上下文侦探 | 检索经验、匹配规则 |

## 设计原则

1. **Agent 是角色**，用名词命名，有身份认同
2. **Command 是动作**，用动词命名，调用 Agent 执行
3. **Agent 代入身份**，以第一人称思考和行动

## 命令与 Agent 的关系

```
命令                    调用的 Agent
────────────────────────────────────
/design            →   Architect
/tasks             →   TaskPlanner
/impl              →   Developer
/extract-experience →  KnowledgeEngineer
/detect-context    →   ContextDetective
```

## 检查点机制

设计和任务分解阶段需要人工确认：

| 阶段 | 状态字段 | 说明 |
|------|----------|------|
| /design | `review_status: pending → approved` | 设计方案需确认 |
| /tasks | `review_status: pending → approved` | 任务清单需确认 |
| /impl | 默认连续执行 | 仅 `confirm_each: true` 时暂停 |

## Developer 调度关系

```
Developer（开发统筹）
    │
    ├─ role: frontend  → 前端实现策略
    ├─ role: backend   → 后端实现策略
    ├─ role: mobile    → 移动端实现策略
    └─ role: devops    → 运维实现策略
```
