---
name: beads-coordinator
description: 在 /tasks --beads 模式下协调任务分解与 Beads 的集成
---

# beads-coordinator

当用户使用 `/tasks --beads` 或明确要求使用 Beads 时，按以下方式工作。

## TaskPlanner 集成

分解任务时**同时创建 Beads 任务**：

1. 创建 Epic：`/beads:epic "<需求名>"`
2. 识别公共任务（数据模型、配置等），创建为 common：
   ```
   /beads:create "公共模块" --parent <epic> --label common
   ```
3. 为每个 Task 创建 Beads 任务，设置依赖：
   ```
   /beads:create "前端登录页" --parent <epic> --label frontend
   /beads:dep add <frontend-id> <common-id>
   ```
4. 同步：`/beads:sync`
5. 在 tasks.md 头部标记：
   ```yaml
   beads_epic: bd-xxxx
   beads_enabled: true
   ```

## Developer 集成

执行任务时**使用 Beads 协调**：

1. 查看就绪任务：`/beads:ready`
2. 开始前认领：`/beads:update <id> --status in_progress`
3. 完成后关闭：`/beads:close <id>`
4. 发现问题时通知其他角色：
   ```
   /beads:create "缺少 avatar_url 字段" --type message --label backend
   ```
5. 结束时同步：`/beads:sync`

## 数据源策略

| 模式 | tasks.md | .beads/ |
|------|---------|---------|
| `--beads` | 只读存档 | 主数据源 |
| 降级 | 主数据源 | 不存在 |

## 降级检测

如果 `/beads:ready` 报错（未安装），则回退到纯 MD 模式。
