---
name: impl
description: "Execute one sdd-kit package PRD scope as code changes. Reads PRD, writes code, runs self-checks, and records DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED through sdd-arbor."
---
# Impl — execute PRD scope
通用约定见 [`../references/conventions.md`](../references/conventions.md)。
Impl 执行一个 package PRD scope：读 PRD 的目标、范围、Acceptance Criteria、Package artifacts 引用、Technical Framing 和 `## Slices`，按顺序连续实现 slice，运行 self-check，记录结果。PRD 是需求 source of truth，impl 不修改 `prd.md`。
## Hard rules
1. 连续执行所有 slices，**不在 slice 之间停顿等待用户确认**。
2. Verification 先落成 required checks；DONE 必须逐项引用 passed check evidence。
3. `prd.md` 和 PRD 引用的 `artifacts/` contract 不静默修改；需要改变时发 NEEDS_CONTEXT 或记录 amendment。
4. 进度通过 `sdd-arbor mark-slice` 写入 `task.json`；不手写 `task.json`，不写第二套执行计划。
5. PRD blocking open questions 或 technical framing 缺失时停止报 NEEDS_CONTEXT，不硬做。
6. Slice 标注 `[existing]` 资源与实际代码不一致时报 NEEDS_CONTEXT；不静默修正。
## 入场
1. 读 `.arbor/tasks/<package>/prd.md`、`task.json`、PRD 引用的 `artifacts/`、wiki 页面，以及 `.arbor/tasks/<package>/slices/` task 文件。
2. 执行 `sdd-arbor derive-required-checks <package>`，把 Verification 固化成 required checks。
3. 按 `task.json.slices` 继续：全 `done` 且有 `impl_result` 则不重复；全 `done` 无结果则 self-check + record；否则按 pending / in_progress 执行；空数组按 PRD 顺序从头。
4. `NEEDS_REWORK` 时读 review 问题清单针对性修复；状态非 doing 时 `sdd-arbor set-status <package> --state doing --actor impl --note "开始执行"`。
Wiki 引用处理见 References；cross-cut 页面漏读视为 silent bug。
## Slice 执行循环
1. 对每个未完成 slice，重读 `slices/S-NNN.md` 和 PRD `Technical Framing`。
2. 围绕 Acceptance 实现，并按 PRD Testing strategy 补测试。
3. 用 `sdd-arbor run-check` / `record-check` 逐项记录 required checks；runnable check 不能当 manual/not_run 省略。
4. Acceptance marker 对账通过后 `sdd-arbor mark-slice <package> --id S-NNN --status done`；有差距则继续做、标 `in_progress`，或最终写 concern。
## Self-check
全部 slice 完成后做 Build + Test + Functional 三层验证，Functional 是必须的。
## 四种结果判定
```
所有 required checks 都有 passed evidence + 所有 marker 对账通过 → DONE
有 required checks blocked/not_run/manual gap + 功能代码已完成      → DONE_WITH_CONCERNS
核心 required checks 无法执行，无法判断核心功能                    → BLOCKED
PRD / Technical Framing 信息缺失 / 冲突                            → NEEDS_CONTEXT
环境、依赖、权限、外部因素阻塞实现或验证                            → BLOCKED
```
DONE_WITH_CONCERNS 适用边界见 References 的 anti-patterns；功能未兑现 PRD 承诺时不要用 concern 掩盖。
## 记录结果
```bash
sdd-arbor record-impl-result <package> \
  --state done|done_with_concerns|needs_context|blocked \
  --summary "<一句话总览本次 impl 范围>" \
  --acceptance "<marker-id>: <证据>" \
  --check chk_001 \
  --concern "<PRD 原意 vs 实际>" \
  ...
```
Acceptance 引用格式：单 marker 用 `S-NNN: <证据>`；多 marker 用 `S-NNN.M: <证据>`。
```
--acceptance "S-001: GET /api/courses 返回 2 条种子 + e2e 通过"
--acceptance "S-004.1: 代报名 API + UI form 走通"
```
## References
- Testing strategy 档位与 TDD loop 见 [`references/tdd.md`](references/tdd.md)。
- Wiki 引用、DONE_WITH_CONCERNS 边界和反模式见 [`references/anti-patterns.md`](references/anti-patterns.md)。
- 状态机与 workflow 细节见 [`references/state-machine.md`](references/state-machine.md) / [`references/workflow.md`](references/workflow.md)。
