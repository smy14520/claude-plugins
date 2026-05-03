---
name: impl
description: "Execute one sdd-kit package PRD scope as code changes. Reads PRD, writes code, runs self-checks, and records DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED through sdd-arbor. Does not modify PRD artifacts."
---

# Impl — execute PRD scope

使用语言：中文。

Arbor helper 入口、路径和常用命令见 [`../references/arbor-helper.md`](../references/arbor-helper.md)；运行前遵守其中约定。

Impl 执行一个 package PRD scope。它读 PRD，按 Slices 顺序连续实现，运行 self-check，并记录结果。执行阶段不需要用户介入——PRD 里该解决的问题都已解决。语义审计属于 review。

## 输入

- `.arbor/tasks/<package>/prd.md`（PRD 是需求和 Slices 的 source of truth）
- `.arbor/tasks/<package>/task.json`（读取 package state；只通过 `sdd-arbor` 更新）

## 流程

1. 读取 PRD 的目标、范围、Acceptance Criteria、Technical Framing、Slices。
2. PRD blocking open questions 或 technical framing 缺失时停止，不要硬做。
3. 用 `sdd-arbor set-status <package> --state doing --actor impl --note "开始执行"` 记录状态。
4. 找到第一个未完成的 slice（`[ ]` 或 `[-]`），开始执行。
5. 连续执行所有 slices，不在 slice 之间停顿等待用户确认。
6. 每完成一个 slice，在 PRD 的 `## Slices` 段将该 slice 标记为 `[x]`。
7. 全部 slices 完成后，运行 self-check。
8. 用 `sdd-arbor record-impl-result <package> --state done|done_with_concerns|needs_context|blocked ...` 记录结果。

## Slices 执行

PRD 的 `## Slices` 段是执行顺序的 source of truth。Impl 按顺序逐个执行，不跳跃。

三种标记：
- `[ ]` 未开始
- `[-]` 部分完成（附简短备注）
- `[x]` 完成

Impl 不创建额外的执行计划文件。Slices 段就是进度记录。

## 断点续作

如果对话中断（上下文窗口满、用户手动停、网络断），恢复时：

1. 读 PRD 的 Slices 段，找到第一个 `[ ]` 或 `[-]` 的 slice。
2. 快速扫描实际代码状态，验证标记是否准确。代码即进度——如果标记说 S-001 完成了，但项目目录是空的，从 S-001 重新来。
3. 如果是 `[-]`（部分完成），读取备注了解上次停在哪里，继续未完成的部分。
4. 继续连续执行剩余 slices。

如果 impl 检测到当前 slice 未完全做完但需要停止（如对话即将结束），在 PRD 中将该 slice 标记为 `[-]` 并附简短备注：

```markdown
- [-] S-002: 认证与 RBAC — 后端 auth API + migration 完成，前端登录页未做
```

## 四种结果

| 状态 | 含义 |
|------|------|
| DONE | PRD scope self-check 通过，无已知妥协 |
| DONE_WITH_CONCERNS | self-check 通过，但有需要 review 知道的顾虑 |
| NEEDS_CONTEXT | PRD / Technical Framing 信息缺失或冲突，继续会变成猜测 |
| BLOCKED | 环境、依赖、权限或外部因素阻塞 |

这四种是 impl 的**结果记录**，不是 package 状态。Package 状态只有 5 种：draft → ready → doing → done → reviewed。

## Self-check

- 从 PRD acceptance criteria、technical framing 和 repo 既有验证方式推导检查。
- 运行命令或验证明确行为。
- 失败时不要声称 DONE。
- 把检查依据和命令写入 `record-impl-result`。

## 规则

- 未运行可用 self-check，不得声称 DONE。
- 连续执行所有 slices，不在中间停顿等用户确认。
- 发现 PRD 决策错误，报告 NEEDS_CONTEXT，不静默改需求。
- 不修改 `prd.md` 的需求内容（只更新 Slices 的进度标记）。
- 不手写 `task.json`。
- 不自动进入 review。
