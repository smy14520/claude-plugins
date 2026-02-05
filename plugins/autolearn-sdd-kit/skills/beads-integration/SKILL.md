---
name: beads-integration
description: Beads 任务管理系统集成，支持并发执行和依赖追踪
---

# Beads Integration

## 环境检测

检测系统是否安装了 Beads：

```bash
which bd
# Windows 备选
where bd
```

## Beads 模式执行流程

### 1. 获取可执行任务

按角色获取任务：

```bash
bd ready --label <role> --json
```

**输出示例**：
```json
[
  {"id": "bd-abc1", "title": "实现登录页面", "labels": ["frontend"], "priority": 1},
  {"id": "bd-abc2", "title": "创建用户组件", "labels": ["frontend"], "priority": 2}
]
```

### 2. 声明任务（避免冲突）

```bash
bd claim <id>
```

### 3. 完成任务

```bash
bd complete <id> [-m "完成说明"]
```

### 4. 查看任务状态

```bash
bd show <id>
```

## 关键命令速查

| 命令 | 用途 |
|------|------|
| `bd ready --label <role>` | 获取指定角色的可执行任务 |
| `bd claim <id>` | 声明任务（防止多 agent 冲突） |
| `bd complete <id>` | 完成任务 |
| `bd show <id>` | 查看任务详情和审计记录 |
| `bd create "标题" --label <role> -p <prio>` | 创建新任务 |
| `bd dep add <child> <parent>` | 设置依赖关系 |

## 并发执行模式

```
Developer 检测到 Beads
    ↓
按角色分组任务
    ↓
并行启动专业开发者：
    FrontendDeveloper → bd claim bd-abc1 ✓
    FrontendDeveloper → bd claim bd-abc2 ✓
    BackendDeveloper  → bd claim bd-def1 ✓
    ↓
并行执行，无冲突
    ↓
全部完成
```

## Markdown 降级模式

当检测不到 `bd` 时：

```
未检测到 Beads
    ↓
降级到 Markdown 模式
    ↓
解析 .claude/context/tasks/*.md
    ↓
串行执行任务
```

## 优先级规则

创建任务时的优先级：

| 优先级 | 含义 | 使用场景 |
|--------|------|---------|
| P0 | 阻塞其他任务 | Contract Request、关键依赖 |
| P1 | 正常优先级 | 大部分任务 |
| P2 | 可延后 | 优化类、非紧急任务 |

## 注意事项

- ⚠️ **必须 claim 后再执行**：避免多 agent 冲突
- ⚠️ **完成后要 complete**：释放任务，解除依赖
- ⚠️ **依赖自动处理**：blocked 任务会自动等待依赖完成
