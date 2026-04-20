# 任务拆分：strict-atomic vs lean

两种显式模式。按任务文件选择（而非按会话）。

## 模式对比

| 维度 | strict-atomic | lean |
|------|---------------|------|
| 单任务最大尺寸 | ≤ 4h | ≤ 1 天 |
| 单任务交付物数 | 恰好 1 个 | 1-3 个相关项 |
| 单任务涉及文件数 | 通常 1-2 个 | 最多约 5 个 |
| 提交粒度 | 1 个任务 = 1 次提交 | 1 个任务 = 1 到少量提交 |
| 适用场景 | 多 agent / 多人；并行 impl；长期工作 | 单人开发；快速原型；有时间盒的工作 |
| 仪式感 | 高（更多任务，显式 DAG） | 较低（更少任务，隐式顺序） |
| 风险 | 对小工作过度拆分 | 任务过粗导致无法精确验证 |

## 如何选择

### 选 strict-atomic 的场景

- 多个人或 agent 将并行执行
- 工作跨度 > 1 周（需要稳定的交接点）
- 关键功能，每个单元需要独立审查
- 用户明确要求并行

### 选 lean 的场景

- 单人，1-2 天的工作量
- 原型/实验，计划可能变化
- 简单的 CRUD 类工作，切分点很明显
- 过度拆分会增加超过价值的仪式感

### 默认值

如果用户未指定：**strict-atomic**。宁可多拆也不要少拆；过粗的任务比过多的任务更糟。

## strict-atomic 规则

1. 每个任务有且仅有**一个** `deliverable:` 条目（不是"三个文件"）
2. 每个任务有且仅有**一个**可验证的验收标准（可以是一个命令）
3. 估算范围 0.5h – 4h
4. 共享模块始终是独立任务
5. 测试可以是独立任务，也可以捆绑在功能任务中——两种都可接受；但在同一文件内保持一致

### 示例（strict-atomic）

```markdown
- id: T-003
  role: backend
  title: "Implement POST /webhook/xhs handler"
  deliverable: "src/webhooks/xhs-handler.ts"
  depends-on: [T-001, T-002]
  acceptance: |
    - file: src/webhooks/xhs-handler.ts exports handleXhsWebhook(req)
    - handler: returns 200 for signed requests, 401 for unsigned
    - no tests in this task (T-005 covers tests)
  estimate: 3h

- id: T-005
  role: test
  title: "Tests for /webhook/xhs handler"
  deliverable: "tests/webhooks/xhs-handler.test.ts"
  depends-on: [T-003]
  acceptance: |
    - run: pnpm test tests/webhooks/xhs-handler.test.ts passes
    - coverage: happy path + invalid signature + duplicate event_id
  estimate: 2h
```

## lean 规则

1. 一个任务可以捆绑相关交付物（"处理器 + 其单元测试"）
2. 仍然有单一的验收标准，但可以是多步的
3. 估算最高 1 天（约 6-8h）
4. 共享模块可以内联到第一个消费任务中；当出现第二个消费方时再提取

### 示例（lean）

```markdown
- id: T-003
  role: backend
  title: "Implement POST /webhook/xhs (handler + tests)"
  deliverable: "src/webhooks/xhs-handler.ts + tests/webhooks/xhs-handler.test.ts"
  depends-on: [T-001, T-002]
  acceptance: |
    - file: src/webhooks/xhs-handler.ts exports handleXhsWebhook(req)
    - run: pnpm test tests/webhooks/xhs-handler.test.ts passes (≥ 3 cases: happy, invalid-sig, replay)
  estimate: 5h
```

## 拆分启发式规则（两种模式通用）

### "我能独立验证什么？" 测试

如果一个交付物必须先验证另一个才能验证自己，那么它依赖于那一个。这个依赖关系就是 `depends-on`。

### "单一关注点" 测试

一个任务应该只有一个变更理由。如果你能想象同一个任务会产生两个 PR，那就拆分。

### "太小" 的气味

如果一个任务：

- 估算 < 30 分钟
- 交付物实际上只有一行（"添加功能开关"）
- 无依赖，也无被依赖

考虑内联到下一个任务中。微型任务会堆积仪式感。

### "太大" 的气味

如果一个任务：

- 估算超过模式上限（strict-atomic 的 4h / lean 的 1 天）
- 交付物是一个列表（"迁移 X，重写 Y，添加 Z"）
- 多条 `notes:` 说"还需要处理……"

拆分。

## 常见拆分分类

从以下 spec 章节推导任务：

| Spec 章节 | 典型任务 |
|----------|---------|
| 数据/状态设计 | 迁移、种子数据、模式测试 |
| 接口契约 | 处理器、控制器、API 客户端、验证器 |
| 约束条件 | 速率限制器、认证中间件、签名验证器 |
| 集成点 | 生产者、消费者、适配器 |
| 测试策略 | 单元/集成/负载测试任务 |
| 可观测性 | 指标发射器、日志增强器、仪表盘 |

将这些作为种子列表；不是每个 spec 都需要每个分类。

## 如何决定任务顺序

依赖 DAG 从谁消费谁的关系中自然产生：

1. 存储优先（迁移、模式）——下游没有它就无法工作
2. 共享工具其次（签名验证器、HTTP 客户端等）
3. 核心逻辑（处理器、领域服务）
4. 集成（事件生产者/消费者）
5. 测试（与 #3 并行或之后，按项目惯例）
6. DevOps 最后（部署配置、功能开关）——除非是阻断性的（如密钥必须在代码运行前存在）

如果你发现自己写了一个引用"待后续添加"内容的任务，那就是一个依赖。显式声明它。

## 重新拆分触发条件

初始任务文件是 lean → impl 遇到阻碍 → 揭示了隐藏依赖 → 对该任务进一步拆分。

允许；做法：

1. 将父任务 `status` 改为 `split`
2. 添加新的子任务，使用新 ID，depends-on 继承父任务的依赖
3. Impl 接手新的原子任务

绝不静默编辑父任务；保留操作轨迹。
