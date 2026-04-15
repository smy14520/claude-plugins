---
name: tasks
description: 任务规划
argument-hint: "[需求名]"
allowed-tools: "Read, Write, Glob, Grep, Task"
model: sonnet
---

你正在执行 `autolearn-sdd-kit` 插件命令 `/autolearn-sdd-kit:tasks`。

用户输入：`$ARGUMENTS`

如果没有提供需求名，直接输出以下用法后结束：

```text
/autolearn-sdd-kit:tasks <需求名>

将设计方案拆为原子级任务清单。
产出：.claude/tasks/<需求名>.tasks.md
前置：/autolearn-sdd-kit:design <需求名> 或 /autolearn-sdd-kit:brainstorming
下一步：/autolearn-sdd-kit:impl <需求名>
```

这条命令的目标，是读取 `.claude/plans/<需求名>-plan.md` 并生成 `.claude/tasks/<需求名>.tasks.md`。对当前项目 `.claude/tasks/**` 的写入属于本命令的预期输出，不要为这些项目内、本地、可逆写入再次请求确认。

## 执行要求

1. 先读取 `.claude/plans/<需求名>-plan.md`；如果文件不存在，明确说明缺少前置设计并结束。
2. 只做一轮最小必要的上下文读取：
   - 直接相关 plan
   - 直接相关模块索引 / 经验资产
   - 一跳相关源码与测试
   不要为了保险起见做全量重复探索。
3. 只允许**一次**委派：启动 `autolearn-sdd-kit:TaskPlanner` agent 生成任务清单。
4. 启动 `TaskPlanner` 后，外层命令不要再次调用同名 skill / command，不要再次启动第二个 `TaskPlanner`，不要做重复拆分。
5. 外层命令的职责只有三件事：
   - 提供最小必要上下文给 `TaskPlanner`
   - 接收 `TaskPlanner` 的任务清单结果
   - 将结果原样整理后落盘到 `.claude/tasks/<需求名>.tasks.md`
6. 一旦 `TaskPlanner` 已经给出完整任务清单，外层不要继续长时间分析、润色或二次重写；只做必要的轻量规范化（如标题、frontmatter、路径一致性）后立即写入。
7. 如果 `TaskPlanner` 输出已经满足结构要求，优先直接落盘，而不是继续“thinking longer”。
8. 输出必须包含：
   - 架构分析
   - Task 列表
   - `role`
   - `stack`
   - `depends_on`
   - `files`
   - 原子级 steps
   - acceptance
7. 默认要求每个 step 足够明确，让执行者无需再做大幅二次规划。
8. 高确定性任务用 strict atomic mode；跨模块任务可用 lean task mode，但仍必须清楚写明文件/模块、动作和验收方式。
9. 禁止出现：`TBD`、`TODO`、`待定`、`实现 XX 功能`、`添加适当处理` 这类模糊表述。
10. step 必须是可执行动作，不要把纯约束句（如“保持 X 不变”“不要修改 Y”）直接写成 step；如需表达约束，应改写为检查/验证动作或放进 acceptance。
11. Task 的 `files` 必须覆盖该 Task 的 steps / acceptance 中点名的所有文件；即使某文件只是边界验证、预期不改，也要列出。
12. 把结果写入 `.claude/tasks/<需求名>.tasks.md`。
13. 完成后输出：
   - tasks 文件路径
   - 任务总数
   - 推荐下一步：`/autolearn-sdd-kit:impl <需求名>`
