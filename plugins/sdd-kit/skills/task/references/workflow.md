# Task 工作流：拆分 / 识别共享 / 排序 / 分配角色

四个原语的详细流程。SKILL.md 给出高层步骤；本文件给出包含边界情况的完整工作流。

---

## 拆分

将 spec 拆解为原子单元。

### 触发短语

- "拆任务 X" / "把 spec X 变成任务"
- "plan X" / "break down spec X"
- "生成 task 计划"

### 完整流程

**步骤 1 — 解析输入**

情况 A：`.claude/specs/<name>.md` 存在

- 读取。检查 `status:` 前置元数据：
  - `accepted` → 继续
  - `draft` / `revising` → 阻断："spec `<name>` 仍是 draft / revising，请先 finalize 再拆任务。"
  - `superseded` → 询问："此 spec 已 superseded by `<new>`. 用新 spec 吗？"

情况 B：没有 spec，用户给出了会话内目标

- 向用户确认理解的目标，一行回复：
  - "理解的目标: `<goal>`. Acceptance: `<criteria>`. 对吗？"
- 用户确认后才继续
- 即使没有 spec 引用也创建任务文件

**步骤 2 — 询问模式**

```
📋 拆任务模式:
  (a) strict-atomic — 每个任务 ≤ 4h, 单一 deliverable, 适合并行 / 多 agent
  (b) lean          — 任务可到 1 天, 适合单人快速推进
  默认: (a) strict-atomic

选哪个？
```

等待用户选择后再继续。将选择记录在任务文件前置元数据中。

**步骤 3 — 拆分**

从 spec 的验收标准 + 数据/状态 + 接口 + 测试策略章节推导单元。每个单元应：

- 是单一的交付物（一个新文件、一个修改的文件、一个端点、一个迁移、一个测试套件）
- 可独立验证（有具体的"完成"检查）
- 在模式的尺寸预算内

典型的种子分类（非穷举）：

- 数据：迁移、模式变更、种子数据
- 核心逻辑：纯函数、领域模型
- 集成：HTTP 处理器、事件生产者、消息消费者
- 横切关注点：配置、密钥、功能开关
- 可观测性：指标、日志、链路追踪
- 测试：单元测试、集成测试、负载测试

**步骤 4 — 分配稳定 ID**

格式：`T-001`、`T-002`、……，零填充到 3 位。ID 只追加；永不重新编号。

编辑已有任务文件时：新任务的 ID = max(已有) + 1。

**步骤 5 — 填写每个任务的必要字段**

对每个任务，按下方 [内容契约](#必要任务字段) 填写：

- `id`
- `role`（默认 `unassigned`）
- `title`（一行，祈使语气）
- `deliverable`（具体制品）
- `depends-on`（ID 列表，可为空）
- `acceptance`（命令或文件状态检查）
- `estimate`（小时数）
- `notes`（可选，用于非显而易见的上下文）

**步骤 6 — 输出草稿供确认**

写入最终文件之前，内联输出任务列表供用户审查：

```
📝 Task draft (strict-atomic, 12 tasks):

T-001 [data/shared] migration: xhs_events table — 1h
T-002 [shared] signature-verifier util — 2h
T-003 [backend] POST /webhook/xhs handler — deps: T-001, T-002 — 3h
...

对吗？(y / edit: 改/删/加哪一条)
```

等待确认/编辑。用户确认前不要写入最终文件。

### 必要任务字段

```yaml
- id: T-001
  role: backend | frontend | data | devops | shared | test | unassigned
  title: "<祈使动作>"
  deliverable: "<具体制品：文件路径 / 端点 / 迁移名称>"
  depends-on: [T-000, ...]      # ID 列表；可为空
  acceptance: |
    - file: src/xxx.ts exists with <signature>
    - run: `pnpm test tests/xxx.test.ts` passes
    - or: `curl -X POST localhost:3000/yyy` returns 200
  estimate: 2h
  notes: |
    可选。给执行者的非显而易见的上下文。
    不要在这里放决策内容；决策属于 spec。
```

### 边界情况

**情况：spec 中有未解决的 `<TODO-DECIDE>` 标记**

阻断："spec `<name>` 仍有 `TODO-DECIDE`。请先回到 spec skill 完成决策，再拆任务。" 提供 grep 行号。

**情况：spec 过于抽象，无法拆分**

询问："spec 的 Acceptance 只有 N 条且偏抽象，我拆出来的会是粗颗粒度。要不要先把 spec 的 Acceptance 细化？" 让用户选择：细化 spec 还是接受粗粒度任务。

**情况：用户想在计划中添加/删除任务**

始终可以。添加：新 ID。删除：在任务块中标记 `status: dropped` 而非删除（保留 git 历史）。修改：原地编辑，但任务 ID 不变。

---

## 识别共享

查找任务间重复的关注点；提取为共享模块任务。

### 何时运行

- 在拆分过程中自动执行，紧跟初始拆分之后
- 或用户显式询问"有哪些公共模块"时

### 流程

**步骤 1 — 扫描任务列表中的重复交付物**

查找模式：

- 3+ 个任务都调用"signature-verifier" → 提取 `T-XXX signature-verifier util`，`role: shared`
- 2+ 个任务触及同一配置加载器 → 提取共享配置任务
- 多个任务引用同一 HTTP 客户端 → 提取共享客户端任务

**步骤 2 — 创建共享任务**

- `role: shared`
- `depends-on:` 通常为 `[]`（共享模块是叶子节点）
- 明确的验收标准：模块可导入且有独立的单元测试

**步骤 3 — 重定向依赖任务**

消费任务将新的共享任务添加到其 `depends-on` 中。

**步骤 4 — 共享任务过多时发出警告**

如果 `shared` 角色任务 > 总数的 30% → 发出警告：

```
⚠️ Shared tasks 占比 X%. 可能存在以下信号:
   - 提前抽象（YAGNI 违反）
   - spec 本身过于模块化，应直接描述更粗的交付物

要继续这种颗粒度吗？
```

### 边界情况

**情况：共享模块过于简单（< 30 行代码）**

不提取为独立任务。内联到第一个消费任务中；添加备注。

**情况：共享模块确实是跨 spec 的**

如果共享模块也被其他 spec（或现有代码）消费，标注："此 shared module 可能 affects 其他 spec，需要 cross-spec 协调。" 标记给用户。

---

## 排序

构建 `depends-on` 关系的 DAG（有向无环图）。

### 流程

**步骤 1 — 收集 depends-on 边**

```
T-003 depends on: T-001, T-002
T-005 depends on: T-003
```

**步骤 2 — 环检测**

DFS 检查环。如发现：

```
❌ 依赖环:
   T-003 → T-005 → T-003

这是设计冲突，不是任务颗粒度问题。建议:
- 拆分其中一个任务
- 或引入中间层抽象 (新增 shared task)
```

**步骤 3 — 输出 DAG 文本**

使用简单的 ASCII 或 mermaid 树形图。不要过度美化。

```
Dependency order:
  T-001 (data)
  T-002 (shared)
    ↳ T-003 (backend) → T-005 (test)
    ↳ T-004 (backend) → T-006 (test)
  T-007 (devops, standalone)
```

**步骤 4 — 识别关键路径**

沿最长依赖链汇总估算值。输出：

```
Critical path: T-002 → T-003 → T-005 → T-006 = 9h
Total estimate: 18h
Max parallel branches: 3
```

### 边界情况

**情况：全部任务都是串行的**

如果无并行可能（每个任务都依赖前一个），标注："所有任务构成线性链——无并行可能。strict-atomic 模式可能过重；考虑 lean。"

**情况：DAG 非常宽（多个叶子节点）**

有利于并行。输出叶子节点列表，让用户知道哪些可以立即开始。

---

## 分配角色

可选地为每个任务标注角色标签。角色仅作参考。

### 标准角色

- `backend` — 服务端代码、API、业务逻辑
- `frontend` — UI、客户端逻辑
- `data` — 模式、迁移、ETL
- `devops` — 基础设施、CI、部署、密钥
- `shared` — 跨角色工具
- `test` — 纯测试交付物
- `unassigned` — 默认，角色不明确时使用

### 流程

**步骤 1 — 从交付物推断**

- `migration: xhs_events table` → `data`
- `POST /webhook/xhs handler` → `backend`
- `src/lib/signature-verifier.ts` → `shared`
- `tests/webhook.test.ts` → `test`
- `terraform: add new topic` → `devops`

**步骤 2 — 请用户确认**

```
📝 Role 分配建议 (可改):
  T-001 data
  T-002 shared
  T-003 backend
  T-004 backend
  T-005 test
  T-006 test
  T-007 devops

修改吗？
```

**步骤 3 — 自定义角色**

用户可以定义项目特定角色（如 `ml`、`mobile-ios`）。接受并记录在任务前置元数据中。

### 边界情况

**情况：角色不明确**

标记 `unassigned` 并在任务的 `notes:` 字段中注明。不要猜测。

**情况：用户跳过角色分配**

可以。所有任务变为 `role: unassigned`。Impl skill 仍然可以工作——它不管角色都会读取任务。
