---
name: beads-coordinator
description: 使用 Beads 进行多 Agent 任务协调，支持 Claude Team 蜂群模式
---

# beads-coordinator

使用 Beads 进行多 Agent 任务协调，支持依赖管理和跨 Agent 通信。

## 前置条件

需要安装 Beads CLI：
```bash
brew install beads
# 或
npm install -g @beads/bd
```

## 环境检测

在使用任何 Beads 功能前，**必须先检测环境**：

```bash
# 检测 Beads 是否安装
command -v bd &> /dev/null && echo "installed" || echo "not_installed"

# 检测项目是否初始化
[ -d ".beads" ] && echo "initialized" || echo "not_initialized"
```

**降级策略**：如果未安装 Beads，应回退到纯 MD 模式，不能阻断任务执行。

---

## 核心操作

### 1. 初始化项目

```bash
bd init
bd hooks install  # 安装 git hooks，自动同步
```

### 2. 创建任务结构

从 task.md 创建 Beads 任务层级：

```bash
# 创建 Epic（需求级别）
bd create "用户登录功能" -p 1 --tag epic

# 创建 Task（任务级别）
bd create "前端登录页面" -p 2 --parent bd-xxxx --tag frontend
bd create "后端 OAuth API" -p 2 --parent bd-xxxx --tag backend

# 创建公共任务（其他任务依赖）
bd create "数据模型定义" -p 3 --parent bd-xxxx --tag common
bd dep add bd-xxxx.2 bd-xxxx.1  # 前端依赖公共任务
bd dep add bd-xxxx.3 bd-xxxx.1  # 后端依赖公共任务
```

### 3. 任务分配与认领

```bash
# 按角色拉取任务（蜂群模式下每个 Agent 使用）
bd ready --tag frontend   # 前端 Agent
bd ready --tag backend    # 后端 Agent

# 认领任务
bd update bd-xxxx.2 --claim
```

### 4. 状态更新

```bash
# 开始任务
bd update <id> --status in_progress

# 完成任务
bd update <id> --status closed

# 添加备注
bd update <id> --notes "已完成登录表单验证"
```

### 5. 跨 Agent 消息

```bash
# 前端发现缺字段，发消息给后端
bd create "需要用户头像字段 avatar_url" \
  --type message \
  --thread backend \
  -p 1

# 后端查看消息
bd ready --type message --tag backend

# 后端回复
bd update <message-id> --status closed --notes "已添加 avatar_url"
```

### 6. 同步

**重要**：每次任务结束必须同步！

```bash
bd sync  # 立即同步到 git
```

---

## 任务生命周期

```
┌─────────┐     ┌─────────────┐     ┌────────┐
│  open   │ ──→ │ in_progress │ ──→ │ closed │
└─────────┘     └─────────────┘     └────────┘
     │                │
     └───── blocked ──┘
```

## 蜂群模式工作流

```
1. TaskPlanner 创建 Epic 和 Tasks (bd create)
2. 每个 Agent 拉取自己角色的任务 (bd ready --tag <role>)
3. 认领任务 (bd update --claim)
4. 执行任务
5. 完成或发消息 (bd update --status / bd create --type message)
6. 同步 (bd sync)
```

---

## 与 task.md 的关系

| 模式 | task.md | .beads/ |
|------|---------|---------|
| Beads 启用 | 只读存档 | 主数据源 |
| 降级模式 | 主数据源 | 不存在 |

Beads 启用时，task.md 头部会包含元数据：

```yaml
---
beads_epic: bd-xxxx
beads_enabled: true
---
```

每个 Task 会包含 beads_id：

```markdown
## Task 1: 前端登录页面
**beads_id**: bd-xxxx.1
**role**: frontend
```
