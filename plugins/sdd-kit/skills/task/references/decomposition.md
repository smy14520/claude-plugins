# 任务拆分：strict-atomic vs lean

两种显式模式。按任务文件选择（而非按会话）。

## 模式对比

| 维度 | strict-atomic | lean |
|------|---------------|------|
| 单任务最大尺寸 | ≤ 4h | ≤ 1 天 |
| 单任务交付物数 | 恰好 1 个 | 1-3 个相关项 |
| 单任务涉及文件数 | 通常 1-2 个 | 最多约 5 个 |
| 适用场景 | 同一 package boundary 内的多 agent / 多人；并行 impl；长期工作 | 单人开发；快速原型；有时间盒的工作 |
| 仪式感 | 高（更多任务，显式 DAG） | 较低（更少任务，隐式顺序） |
| 大需求处理 | 先验证 brainstorm 的需求澄清与 map 的 package sizing；若仍是单 package，再通过 milestone + T-xxx | 先验证 brainstorm 的需求澄清与 map 的 package sizing；若仍是单 package，再通过较粗的 slice task |

## 如何选择

### 选 strict-atomic 的场景

- 多个人或 agent 将并行执行
- 工作跨度 > 1 周
- 关键功能，每个单元需要独立审查
- 用户明确要求并行

### 选 lean 的场景

- 单人，1-2 天工作量
- 原型 / 实验，计划可能变化
- 需求已经在 PRD 中收敛得较清楚
- 过度拆分会增加超过价值的仪式感

### 默认值

如果用户未指定：**strict-atomic**。

## Package sizing secondary guard

Brainstorm 应先澄清需求并形成 package PRD，map 应先完成 split 后 child package 的 boundary sizing。Task 在选择 strict-atomic / lean 和拆 T-xxx 前，只验证这个上游判断是否存在且仍可信。

### 判定为 fits_package

满足以下条件时，继续在当前 package 内拆 T-xxx：

- 交付物可以在一个 branch/worktree/PR 中 review
- 多 agent 并行主要是同一边界内的短期协作
- slice 共享同一发布/回滚节奏
- package-local T-xxx 数量不会膨胀到难以 review

### 判定为 split_recommended

出现以下信号时，说明上游应回到 map/package graph；task 应停止，不要继续生成长 T-xxx 列表：

- 一个 PRD 覆盖多个可独立 PR 的业务域
- 某个 slice 需要独立 worktree/branch/PR 或独立发布节奏
- 多个 agent 可以长期并行，不应挤在同一 worktree/branch
- T-xxx 会超过约 8-10 个
- 关键路径很长，但旁路模块明显独立
- 涉及前台 / 后台 / 交易 / 营销 / 权限等多个子系统
- 某些 slice 可以单独上线、验收、回滚

输出应是 package graph，而不是 T-xxx 列表。例如：

```text
knowledge-paid-system
├── knowledge-course-core
├── knowledge-course-experience  depends on knowledge-course-core
├── knowledge-balance-order       depends on knowledge-course-core
├── knowledge-marketing-sale      depends on knowledge-balance-order
└── knowledge-marketing-group     depends on knowledge-balance-order
```

## milestone / child task 启发式

只有 package boundary 成立后，才判断 milestone。以下信号出现时，优先先写 milestone 再拆 task：

- PRD 已列出多个独立交付物或切片
- 需求跨多个表层（backend / frontend / data / docs）
- 一个总任务很难直接判断 ready / blocked
- 有明显的先后阶段（基础设施 → 核心行为 → 验证 / 文档）

### 例子

| Brainstorm 区块 | 典型任务种子 |
|-----------------|-------------|
| 关键场景 / 用户流 | handler / controller / page / form |
| 交付物清单 | 文件、端点、模块、迁移 |
| 拆解线索 / 切片建议 | milestone / shared module / sequence |
| 风险 / 开放问题 / 假设 | ready-check / blockers |
| Sources | task-local sources |

## strict-atomic 规则

1. 每个任务有且仅有一个 `deliverable:`
2. 每个任务有显式 `context:` / `sources:` / `ready-check:`
3. 估算范围 0.5h – 4h
4. 共享模块优先独立成任务
5. 如果某个 open question 只阻塞一个任务，只把它写进该任务的 `ready-check`，不要阻塞整个任务文件

## lean 规则

1. 一个任务可以捆绑相关交付物
2. 仍需 task-local context 与 sources
3. 估算最高 1 天（约 6-8h）
4. milestone 可以更少，但仍建议对大 feature 至少分 2-3 个切片

## 共同启发式

### "我能独立验证什么？" 测试

如果一个交付物必须先验证另一个才能验证自己，那么它依赖于那一个。这个依赖就是 `depends-on`。

### "执行者还需要回到 PRD 吗？" 测试

如果某个任务需要执行者回去读 PRD 才能知道自己做什么，说明 `context:` 仍不够。

### "哪些来源真的和这个任务相关？" 测试

不要把 PRD 的全部来源都搬进任务。只列与本任务有关的 `SRC-*`。

### "需要独立 PR / worktree 吗？" 测试

如果一个 slice 需要独立 branch/worktree/PR 或独立发布节奏，它不应只是 T-xxx，应提升为新的 package 并由 map 维护依赖。如果它只是同一 package 内的验收/review 切片，保留为 T-xxx。

### "T-xxx 太多是不是问题？" 测试

T-xxx 多不必然错误，但如果数量超过约 8-10 个，必须重新检查 package boundary。若这些任务分属多个可独立 review / merge / rollback 的业务域，应拆 package；只有当它们确实共享同一个 PR/worktree 边界时，才保留为一个 package 内的 milestone + T-xxx。

### "太大" 的气味

如果一个任务：

- 估算超过模式上限
- 同时覆盖多个里程碑目标
- 有多个互不相干的来源束
- `context:` 写成了半页文档

拆分。
