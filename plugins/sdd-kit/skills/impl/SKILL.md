---
name: impl
description: "Execute a task (or ad-hoc goal) as actual code changes. Picks a task from `.claude/tasks/<name>.tasks.md`, writes code to meet its acceptance, runs its own acceptance commands (self-check, not semantic review), reports with a strict 4-state machine (DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED). Prioritizes task-local context and sources over rereading the whole brainstorm. Never claims DONE without passing `acceptance:` commands. Semantic audit against brainstorm + diff is the review skill's job. Appends status line to the task file. Works without a task file too. Invoke only on explicit user request (e.g. '用 impl skill 执行 <task-id>')."
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

- 读取任务（从文件或会话中）
- 以 `deliverable + acceptance + context + sources + ready-check` 为主执行
- 在需要时仅读取 brainstorm 作为背景，而不是重新做高层方案判断
- 运行任务自身的验收命令（**自检**，机械性）
- 以四状态机报告状态
- **不**修改任务定义；**不**做高层设计决策；**不**对 brainstorm 做语义审计

## 四个原语

### 🎯 Pick — 选择任务

触发："实施 T-003"、"执行下一个 task"、"run next task"。

1. 定位 `.claude/tasks/<file>.tasks.md`
2. 读取任务列表 + 状态日志
3. 选择下一个可执行任务：`depends-on` 已满足，且 `ready-check` 不阻塞
4. 向用户确认后开始

### 🔨 Execute — 编写代码

触发：Pick 之后，或直接开始。

1. 读取任务的 `deliverable + acceptance + context + sources + notes`
2. 如 task 仍不足以解释局部背景，可读取对应 brainstorm 作为背景
3. 编写最小变更，以通过 acceptance 为目标
4. 若遇到歧义，区分：
   - task-local 信息缺失 / 冲突 → `NEEDS_CONTEXT`
   - 环境阻塞 → `BLOCKED`

### ✅ SelfCheck — 运行任务自身的验收命令

触发：Execute 之后，始终在报告 DONE 之前执行。

1. 运行任务 `acceptance:` 中的每一条命令 / 谓词
2. 捕获退出码 + 相关输出
3. 任一失败 → 不得声称 DONE
4. SelfCheck 范围严格等于 `acceptance:`

### 📤 Report — 发出状态

触发：SelfCheck 之后，或在 BLOCKED / NEEDS_CONTEXT 时。

1. 分类为：DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED
2. 将状态行追加到任务文件的 `## Status log`
3. 向用户输出结构化摘要，并建议下一步
4. 若状态为 `DONE_WITH_CONCERNS` 或 `BLOCKED`，可建议用户是否沉淀 wiki，但绝不自动入库

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
3. **优先信任 task-local context** —— 不是每次都回到 brainstorm 重读全局文档。
4. **禁止修改任务定义** —— impl 只追加状态日志。
5. **一次一个任务** —— 完成 + 报告后再选下一个。
6. **SelfCheck = 验收** —— 语义审计属于 review。
7. **禁止自动推进到下一任务** —— 除非用户明确说继续。

## 初始化

若 `.claude/tasks/` 不存在：impl 无法运行任务模式，仅支持临时模式。

## 本 skill 不做的事

- 不修改 brainstorm
- 不修改任务定义
- 不因"显而易见"而跳过 SelfCheck
- 不对 brainstorm / diff 做语义审计（那是 `review`）
- 不自动调用 `review`

## 何时不激活

- 任务仍被 `ready-check` 阻塞
- 用户仍在 research / brainstorm / task 阶段
- 实际无需代码变更（纯讨论）
