# Task 工作流：拆分 / 识别共享 / 排序 / 分配角色

四个原语的详细流程。SKILL.md 给出高层步骤；本文件给出包含边界情况的完整工作流。

---

## 拆分

将 brainstorm（或兼容 legacy spec）拆解为 milestone + executable task。

### 触发短语

- "拆任务 X" / "把 brainstorm X 变成任务"
- "plan X" / "break down brainstorm X"
- "生成 task 计划"

### 完整流程

**步骤 1 — 解析输入**

情况 A：`.claude/brainstorms/<name>.md` 存在

- 读取。检查前置元数据：
  - `ready-for-task` → 继续
  - `draft` / `revising` → 允许继续，但只冻结不被其 open question 阻塞的任务
  - `superseded` → 询问是否改用新文档

情况 B：只有 legacy `.claude/specs/<name>.md`

- 读取并标记 `source_type: legacy-spec`
- 兼容拆解，但提示用户新格式首选 brainstorm

情况 C：无文件，用户给出会话内目标

- 先确认目标与 acceptance
- 创建 ad-hoc task 文件

**步骤 2 — 询问模式**

```text
📋 拆任务模式:
  (a) strict-atomic — 每个任务 ≤ 4h, 单一 deliverable, 适合并行 / 多 agent
  (b) lean          — 任务可到 1 天, 适合单人快速推进
  默认: (a) strict-atomic
```

**步骤 3 — 先决定是否需要 milestone**

若 brainstorm 中出现以下信号，先分 milestone：
- 多个交付物簇
- 多个切片 / 阶段
- 明显的前后顺序
- 跨 backend / frontend / data / docs

否则，直接生成平铺任务列表。

**步骤 4 — 生成任务草稿**

从以下区块推导：
- 关键场景 / 用户流
- 交付物清单
- 拆解线索 / 实现切片建议
- 风险 / 开放问题 / 假设
- Sources

每个任务至少填写：
- `id`
- `milestone`
- `role`
- `title`
- `deliverable`
- `depends-on`
- `context`
- `sources`
- `ready-check`
- `acceptance`
- `estimate`
- `notes`

**步骤 5 — 输出草稿供确认**

在用户确认前先给出任务草稿摘要。确认后再写入最终文件。

### 边界情况

**情况：brainstorm 仍有开放问题**

不要机械阻断。只要某个问题不阻塞某个具体任务，就允许继续拆解。把阻塞写进该任务的 `ready-check`。

**情况：brainstorm 太空，无法拆分**

提示用户回到 brainstorm 补充：
- 关键场景
- 交付物清单
- 拆解线索

**情况：来源太多**

只保留和该任务直接相关的 `SRC-*`。不要把整个 brainstorm 附录复制进每个任务。

---

## 识别共享

查找任务间重复关注点；提取为共享模块任务。

### 流程

1. 扫描多个任务的 deliverable / context
2. 找出真正复用、且可以独立验证的共享能力
3. 创建 `role: shared` 任务
4. 消费任务追加 `depends-on`
5. 若 shared 任务超过总数的 30%，提示可能过度抽象

---

## 排序

构建 milestone 与 `depends-on` DAG。

### 流程

1. 收集所有依赖边
2. 环检测
3. 输出 ASCII 依赖图
4. 输出关键路径、可并行分支、当前 ready 任务列表

---

## 分配角色

标准角色：
- `backend`
- `frontend`
- `data`
- `devops`
- `shared`
- `test`

如用户未指定，可自动建议。
