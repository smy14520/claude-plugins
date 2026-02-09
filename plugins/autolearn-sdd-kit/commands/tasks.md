---
command: /tasks
description: 任务规划，支持 --beads 多 Agent 协调
agent: TaskPlanner
---

# /tasks

调用 **TaskPlanner**（任务规划师）进行任务分解。

## 用法

```bash
/tasks <需求名>           # 标准模式
/tasks <需求名> --beads   # Beads 增强模式
```

## 参数

| 参数 | 说明 |
|------|------|
| `--beads` | 启用 Beads 多 Agent 协调模式 |

## 执行

### 标准模式

1. 读取 `./.claude/plans/<需求名>-plan.md` 设计方案
2. 调用 **TaskPlanner** Agent
3. 分解任务，每个 Task：
   - 标注 `role`（frontend / backend / mobile / devops）
   - 标注 `stack`（技术栈）
   - 拆分 3-5 个可执行小点
4. 产出 `./.claude/tasks/<需求名>.tasks.md`

### Beads 增强模式

1. **检测环境**：确认 `bd` 命令可用
   - 未安装则降级到标准模式
2. **初始化**：`bd init && bd hooks install`
3. 读取设计方案
4. 调用 **TaskPlanner** Agent
5. **提取公共任务**：识别共享模块，标记为 common
6. **创建 Beads 任务**：
   - Epic：`bd create "<需求名>" -p 1 --tag epic`
   - Tasks：`bd create "<任务>" -p 2 --parent <epic> --tag <role>`
   - 依赖：`bd dep add <child> <parent>`
7. **同步**：`bd sync`
8. 产出：
   - `.beads/` ← 主数据源
   - `./.claude/tasks/<需求名>.tasks.md` ← 只读存档

## 完成后

### Beads 模式

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 任务规划已完成（Beads 模式）

Epic: bd-xxxx
共 X 个 Task，涉及角色：common, frontend, backend

.beads/ ← 主数据源
.claude/tasks/<需求名>.tasks.md ← 只读存档

下一步: /impl <需求名>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 标准模式 / 降级模式

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 任务规划已完成

共 X 个 Task，涉及角色：frontend, backend

文件: ./.claude/tasks/<需求名>.tasks.md

下一步: /impl <需求名>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
