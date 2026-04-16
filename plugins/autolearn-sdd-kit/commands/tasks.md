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
3. **已批准 design 是任务契约**：如果 `.claude/plans/<需求名>-plan.md` 已明确要求某个流程、弹窗、管理能力、交互或测试边界，TaskPlanner 不得静默删减、降级成“首版不做”或改写范围；如发现设计与代码现实冲突，必须显式指出，而不是私自缩水。
4. 优先按“最小完整交付切片”拆任务，而不是按技术层、文件类别或实现介质机械拆分。每个 Task 应该对应一个可独立验证的行为增量，而不是某一类文件的归类集合。
5. 只有当某部分本身是共享产物、能独立验证、并且明确作为其它 Task 的前置依赖时，才单独拆成 Task。
6. 如果某个 Task 负责生产前置产物，任何消费这些产物的 Task 都必须依赖它；不要出现 producer 在后、consumer 在前的依赖倒置。
6. Task 的 `files` 必须覆盖所有 step / acceptance 中点名的文件，**特别是新建测试文件**，不能遗漏。
7. 同一文件默认应有清晰主归属 Task；兄弟 Task 默认不要重复占用同一批文件，除非能明确说明 producer/consumer 关系或该交叉对完整行为切片不可避免。
8. 外层命令可以委派 `autolearn-sdd-kit:TaskPlanner` 生成任务清单，但必须把它视为**本轮唯一的 authoritative draft**。
9. 禁止递归或失控式重复委派：外层不要再次调用同名 skill / command，不要把同一需求重新丢给第二个 `TaskPlanner` 以混合多个版本结果，也不要在未处理当前 draft 缺陷前直接重跑一轮拆分。
10. 如果 `TaskPlanner` 结果存在问题，优先在当前 authoritative draft 上修正思路：
   - 能轻量规范化的就直接规范化后落盘
   - 发现 design 缺口或现实冲突时，明确指出并回到 design/review
   - 不要用“再起一个 planner 试试”代替 review
11. 外层命令的职责只有三件事：
   - 提供最小必要上下文给 `TaskPlanner`
   - 接收 `TaskPlanner` 的任务清单结果
   - 将结果原样整理后落盘到 `.claude/tasks/<需求名>.tasks.md`
12. 一旦 `TaskPlanner` 已经给出完整任务清单，外层不要继续长时间分析、润色或二次重写；只做必要的轻量规范化（如标题、frontmatter、路径一致性）后立即写入。
13. 如果 `TaskPlanner` 输出已经满足结构要求，优先直接落盘，而不是继续“thinking longer”。
14. 输出必须包含：
   - 架构分析
   - Task 列表
   - `role`
   - `stack`
   - `depends_on`
   - `files`
   - 原子级 steps
   - acceptance
15. 默认要求每个 step 足够明确，让执行者无需再做大幅二次规划。
16. 高确定性任务用 strict atomic mode；跨模块任务可用 lean task mode，但仍必须清楚写明文件/模块、动作和验收方式。
17. 禁止出现：`TBD`、`TODO`、`待定`、`实现 XX 功能`、`添加适当处理` 这类模糊表述。
18. step 必须是可执行动作，不要把纯约束句（如“保持 X 不变”“不要修改 Y”）直接写成 step；如需表达约束，应改写为检查/验证动作或放进 acceptance。
19. Task 的 `files` 必须覆盖该 Task 的 steps / acceptance 中点名的所有文件；即使某文件只是边界验证、预期不改，也要列出。
20. 把结果写入 `.claude/tasks/<需求名>.tasks.md`。
21. 完成后输出：
   - tasks 文件路径
   - 任务总数
   - 推荐下一步：`/autolearn-sdd-kit:impl <需求名>`
