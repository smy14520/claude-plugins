---
name: impl
description: "Execute a package-local T-xxx task (or ad-hoc goal) as actual code changes inside the package execution boundary. Picks a T-xxx from `.arbor/tasks/<name>/task.md`, reads lifecycle metadata from `.arbor/tasks/<name>/task.json`, consumes package-local PRD/context as needed, writes code to meet acceptance, runs self-check commands, and updates task state through `tools/arbor.py` with DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED. Never claims DONE without passing `acceptance:` commands. Does not create per-T-xxx branch/worktree/PR. Semantic audit is review's job. Invoke only on explicit user request (e.g. '用 impl skill 执行 <package> 的 T-001')."
---

# Impl — 任务执行器（四状态报告）

将任务执行为代码。在声称 DONE 之前，必须运行任务自身的验收命令。绝不可以将 BLOCKED 悄悄降级为 DONE。

## 在五阶段工作流中的定位

```text
research → brainstorm → task → [impl] → review
                                 ↓          ↑
                                 └─ 仅自检（机械性）
                                    语义审计属于 review skill
```

Impl 是**执行**阶段。它：

- 读取任务 package（`prd.md` / `task.md` / `task.json` / `context/impl.jsonl`）
- 遵循当前 repo 的实际实现结构，以及 package PRD/task 中已明确的局部约束
- 以 `deliverable + acceptance + context + sources + ready-check` 为主执行
- 在需要时仅读取 package-local `prd.md` 作为背景，而不是重新做高层方案判断
- 运行任务自身的验收命令（**自检**，机械性）
- 以四状态机报告状态
- 通过 `tools/arbor.py` 更新 lifecycle 元数据
- **不**修改 PRD；**不**修改任务定义；**不**做高层设计决策；**不**做语义审计

## 四个原语

### 🎯 Pick — 选择任务

触发："实施 <package> 的 T-003"、"执行 <package> 下一个 task"、"run next task for <package>"。

1. 先确认 package，再确认 package-local T-xxx；不要把裸 `T-001` 当作全局唯一任务
2. 定位 `.arbor/tasks/<name>/task.md`
3. 读取任务定义 `task.md` + 生命周期元数据 `task.json` + `context/impl.jsonl` + `context/sources.jsonl`
4. 检查 `task.json.execution`，确认当前工作区/branch/worktree 属于 package boundary；不为 T-xxx 创建独立 branch/worktree/PR
5. 若 `task.json.active_task` 指向未完成任务，优先恢复该任务；否则选择下一个可执行任务：`depends_on` 已满足，且 `ready-check` 不阻塞
6. 若 `task.json.next_action.skill` 不是 `impl`，先说明当前推荐动作与原因
7. 向用户确认后开始，并用 `arbor.py set-status <name> --task T-xxx --state in_progress --actor impl --note "implementation started"` 记录状态

### 🔨 Execute — 编写代码

触发：Pick 之后，或直接开始。

1. 读取任务的 `deliverable + acceptance + context + sources + notes`
2. 如 task-local context 仍不足以解释局部背景，可读取同 package 的 `prd.md` 作为背景
3. 按当前 repo 的源码/测试结构写代码；若 package PRD/task 明确了落点，优先遵循
4. 编写最小变更，以通过 acceptance 为目标；产品源码/测试必须写到 repo implementation tree，不得写入 `.arbor/tasks/<package>/`
5. 若 task/PRD 未明确源码落点且当前 repo 也无法推断（例如空仓库且当前 task 不是建立项目基线），停止为 `NEEDS_CONTEXT`，不要创建孤立 demo 文件
6. 若任务带 `source_amendment`，读取对应 AMD，只实现该增量修正，不改写旧 PRD/task
7. 若遇到歧义，区分：
   - task-local 信息缺失 / 冲突 → `NEEDS_CONTEXT`
   - 环境阻塞 → `BLOCKED`

### ✅ SelfCheck — 运行任务自身的验收命令

触发：Execute 之后，始终在报告 DONE 之前执行。

1. 运行任务 `acceptance:` 中的每一条命令 / 谓词
2. amendment-linked task 必须覆盖 increment acceptance + regression acceptance
3. 捕获退出码 + 相关输出
4. 任一失败 → 不得声称 DONE
5. SelfCheck 范围严格等于 `acceptance:`
6. 若 acceptance 缺失、不可运行，或与当前 repo 实际命令冲突，停止为 `NEEDS_CONTEXT` / `BLOCKED`；不要自造替代验收后声称 DONE

### 📤 Report — 发出状态

触发：SelfCheck 之后，或在 BLOCKED / NEEDS_CONTEXT 时。

1. 分类为：DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED
2. 使用 `tools/arbor.py` 更新 `.arbor/tasks/<name>/task.json` 中对应 T-xxx 的 `state`、`updated_at`、顶层 `state/current_phase/active_task/next_action` 与 `phase_history`
3. 若有新的 implementation context，使用 `arbor.py add-context <name> --type impl ...` 追加 JSONL packet
4. 向用户输出结构化摘要，并建议下一步
5. 若状态为 `DONE_WITH_CONCERNS` 或 `BLOCKED`，可建议用户是否沉淀 wiki，但绝不自动入库

## 四种状态

| 状态 | 含义 |
|------|------|
| **DONE** | 所有验收命令通过，无已知妥协 |
| **DONE_WITH_CONCERNS** | 验收通过，但执行者发现了技术债务 / 妥协 / 非理想路径 |
| **NEEDS_CONTEXT** | task-local 所需信息缺失或冲突，无法继续 |
| **BLOCKED** | 环境 / 依赖 / 外部因素阻碍继续推进 |

## 核心规则

1. **禁止未经验证的声明** —— 未跑完 acceptance 绝不 DONE。
2. **禁止静默做高层设计选择** —— 真正影响行为的选择应在 brainstorm / task 冻结。
3. **优先信任 task-local context** —— 不是每次都回到 PRD 重读全局文档。
4. **禁止修改任务定义** —— impl 只通过 `arbor.py` 更新 `task.json` 的执行状态元数据。
5. **一次一个 T-xxx** —— 完成 + 报告后再选下一个；T-xxx 只在当前 package 内唯一。
6. **Package 是执行边界** —— 代码变更进入 package branch/worktree；不要为 T-xxx 默认创建独立 PR。
7. **单个 DONE 不等于 package 完成** —— DONE 只表示当前 T-xxx 自检通过，package readiness 由所有 required T-xxx 的 review 聚合而来。
8. **SelfCheck = 验收** —— 语义审计属于 review。
9. **Amendment 是增量实现** —— 不为了“看起来一致”去改旧 PRD/task；只实现新 T-xxx。
10. **禁止自动推进到下一任务** —— 除非用户明确说继续。
11. **不手写 JSON 状态** —— 除非脚本不可用且用户明确允许手动修复。

## 初始化

若 `.arbor/tasks/` 不存在：impl 无法运行 task package 模式，仅支持临时模式。

## 本 skill 不做的事

- 不修改 PRD / `prd.md`
- 不修改任务定义 / `task.md`
- 不因"显而易见"而跳过 SelfCheck
- 不对 PRD / diff 做语义审计（那是 `review`）
- 不自动调用 `review`

## 何时不激活

- 任务仍被 `ready-check` 阻塞
- 用户仍在 research / brainstorm / task 阶段
- 实际无需代码变更（纯讨论）
