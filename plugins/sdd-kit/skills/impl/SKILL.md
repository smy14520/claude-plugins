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

1. 读取 PRD 的目标、范围、Acceptance Criteria、Technical Framing（含 Testing strategy）、Slices。
2. 检查 Slices 状态：
   - 所有 slice 已 `[x]` 且 `task.json` 已有 impl_result → package 已完成，不重复执行。
   - 所有 slice 已 `[x]` 但没有 impl_result → 直接跳到 self-check（步骤 9）。
   - 存在 `[ ]` 或 `[-]` → 正常执行（步骤 3 起）。
3. PRD blocking open questions 或 technical framing 缺失时停止，不要硬做。
4. 存量项目的 slice 包含技术锚点时，先验证锚点描述的现有结构仍然成立（表是否存在、模块接口是否匹配、设计模式是否如 PRD 所述），再动刀。发现不一致时报告 NEEDS_CONTEXT，不要硬改。
5. 用 `sdd-arbor set-status <package> --state doing --actor impl --note "开始执行"` 记录状态（已处于 doing 时跳过）。
6. 找到第一个未完成的 slice（`[ ]` 或 `[-]`），开始执行。
7. 连续执行所有 slices，不在 slice 之间停顿等待用户确认。
8. 每完成一个 slice，在 PRD 的 `## Slices` 段将该 slice 标记为 `[x]`。
9. 全部 slices 完成后，运行 self-check。
10. 用 `sdd-arbor record-impl-result <package> --state done|done_with_concerns|needs_context|blocked ...` 记录结果。

## Testing strategy

读取 PRD Technical Framing 中的 Testing strategy 字段，按选择的档位执行：

- **核心路径测试**：每个 slice 完成后，补该 slice 涉及的关键路径和边界 case 测试，运行并确认全部通过后才标记 `[x]`。外部依赖用 mock/fake。
- **TDD 驱动**：每个 slice 先写测试再写实现，按 `references/tdd.md` 的 red-green loop 执行，绿灯后才标记 `[x]`。外部依赖用 mock/fake。
- **最小验收**：全部 slice 完成后，跑 happy path 验证功能跑通。

测试框架和工具由 Technical Framing 的 stack 决定（AI 根据项目技术栈自行选择），sdd-kit 不指定具体工具。

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
3. 读已有测试文件——测试是前面 slice 设计决策的最好文档，能快速了解已建立的接口契约、数据结构和预期行为，避免后续 slice 与前面的设计意图矛盾。
4. 如果是 `[-]`（部分完成），读取备注了解上次停在哪里，继续未完成的部分。
5. 继续连续执行剩余 slices。

如果是 review NEEDS_REWORK 后回到 impl：

1. 读 `task.json` 的 `review_result`，了解 review 给出的具体问题清单和 verdict 理由。
2. 针对性修复 review 指出的问题，不要从头重新执行所有 slice。
3. 修复完成后重新运行 self-check，用 `record-impl-result` 记录新结果。

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

Self-check 必须覆盖三层，不能只跑其中一层就声称 DONE：

1. **构建通过** — 项目能正常编译/构建，无报错。
2. **测试通过** — 按 Testing strategy 写的测试全部通过。没有测试跳过或忽略的关键失败。
3. **功能验证** — 实际启动应用，验证核心路径可用：
   - Web 项目：启动 dev server，用浏览器或 playwright 访问关键页面，确认能正常交互
   - API 项目：启动服务，用 curl 或测试客户端验证关键接口的请求和响应
   - CLI 工具：运行关键命令，检查输出符合预期
   - 如果环境限制无法验证（如缺少数据库、缺少外部服务），明确记录为 DONE_WITH_CONCERNS 并说明原因，不要假装验证过了

构建通过 + 测试通过 ≠ DONE。功能验证是必须的。

功能验证失败时：先诊断原因并尝试修复，修复后重新运行三层验证。反复修复仍无法通过时，记录为 DONE_WITH_CONCERNS（问题明确但非阻塞）或 BLOCKED（环境/依赖阻塞），不要假装通过。

把三层的检查依据和命令结果写入 `record-impl-result`。

## 规则

- 未运行可用 self-check，不得声称 DONE。
- 连续执行所有 slices，不在中间停顿等用户确认。
- 发现 PRD 决策错误，报告 NEEDS_CONTEXT，不静默改需求。
- 不修改 `prd.md` 的需求内容（只更新 Slices 的进度标记）。
- 不手写 `task.json`。
- 不自动进入 review。
