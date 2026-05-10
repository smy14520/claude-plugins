---
name: impl
description: "Execute one sdd-kit package PRD scope as code changes. Reads PRD, writes code, runs self-checks, and records DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED through sdd-arbor."
---

# Impl — execute PRD scope

通用约定见 [`../references/conventions.md`](../references/conventions.md)。

Impl 执行一个 package PRD scope：读 PRD 的目标、范围、Acceptance Criteria、Package artifacts 引用、Technical Framing 和 `## Slices`，按顺序连续实现 slice，运行 self-check，记录结果。PRD 是需求 source of truth，impl 不修改 `prd.md`。

## Hard rules

1. 连续执行所有 slices，**不在 slice 之间停顿等待用户确认**。
2. 未运行可用 self-check，不得声称 DONE。
3. `prd.md` 和 PRD 引用的 `artifacts/` contract 不静默修改；需要改变时发 NEEDS_CONTEXT 或记录 amendment。
4. 进度通过 `sdd-arbor mark-slice` 写入 `task.json`；不手写 `task.json`，不写第二套执行计划。
5. PRD blocking open questions 或 technical framing 缺失时停止报 NEEDS_CONTEXT，不硬做。
6. Slice 标注 `[existing]` 资源与实际代码不一致时报 NEEDS_CONTEXT；不静默修正。

## 入场

1. 读 `.arbor/tasks/<package>/prd.md`、`task.json`、PRD 引用的 `artifacts/`、PRD 引用的 wiki 页面（见 Wiki 引用处理）。
2. 读 `.arbor/tasks/<package>/slices/` 目录下的 task 文件（`S-001.md`、`S-002.md`...），了解每个 slice 的 Acceptance、Approach、Verification。
3. 读 `task.json.slices` 判断进度：
   - 全 `done` 且有 `impl_result` → 已完成，不重复执行。
   - 全 `done` 但无 `impl_result` → 直接 self-check + 记录。
   - 有 `pending` / `in_progress` → 正常执行。
   - 数组空或不存在 → 全部 pending，按 PRD `## Slices` 顺序从头开始。
4. 若 `review_result.state` 是 `NEEDS_REWORK`（CLI 参数 `needs_rework`），读问题清单针对性修复，不从头执行 slice。
5. 状态非 doing 时 `sdd-arbor set-status <package> --state doing --actor impl --note "开始执行"`。

代码即进度——`task.json.slices` 标记与项目实际状态不符时以代码为准。读已有测试是了解前面 slice 接口契约的捷径。

## Wiki 引用处理

PRD Technical Framing 写了 `详见 [[...]]` 形式的 wikilink 时：

- `cross_cut` 页面：漏读 = silent bug。`sdd-arbor wiki-collect --query "<kw>"` 读页面，verify 位置 / 命名 / 注册机制仍适用；不一致按 PRD fallback 调研代码。
- 其它 type（module / entity / gotcha / decision / source）：按 orientation 读，不逐一 verify。

## Slice 执行循环

对每个未完成 slice：

1. 读对应的 `slices/S-NNN.md` task 文件。以 **Acceptance** 的 Then 条件为目标，**Approach** 为推荐路径（可偏离），**Verification** 命令为 done 标准。
2. 按 PRD Testing strategy 档位实现 + 测试（TDD：先测后写；核心路径：实现后补关键路径 + 边界；最小验收：happy path 跑通）。
3. 运行 task 文件的 Verification 命令，确认通过。
4. 对账：Acceptance 的每条 Then 是否有对应可观测产物？特别注意 negative invariant——只证 positive action 不算对账通过。
5. `sdd-arbor mark-slice <package> --id S-NNN --status done`；有差距用 `--status in_progress --note "<差距>"` 继续做，或接受妥协在最后 record 时写 `--concern`。

`task.json.slices` 的三态：`pending` 未开始 / `in_progress` 部分完成（附备注说明停在哪里）/ `done` 完成。

## Self-check

全部 slice 完成后按序跑：

| 层 | 内容 | 失败处理 |
|---|---|---|
| A. Build | 项目能编译 / 构建无报错 | 修复；反复失败 → NEEDS_CONTEXT / BLOCKED |
| B. Test | 按 Testing strategy 的测试全部通过 | 修复；反复失败 → NEEDS_CONTEXT / BLOCKED |
| C. Functional | 按 Technical Framing 的 stack / runtime 启动并验证核心路径 | 诊断修复；反复失败按判定表选结果 |

Build + Test 通过不等于 DONE。Functional 是必须的。把三层的依据与命令结果传给 `record-impl-result`。

## 四种结果判定

```
A/B/C 全通过 + 所有 marker 对账通过                    → DONE
A/B/C 通过 + 至少一条 concern                           → DONE_WITH_CONCERNS
C 因非阻塞环境限制无法完整验证（功能已实现）             → DONE_WITH_CONCERNS
C 因环境/依赖导致无法完成或无法判断核心功能              → BLOCKED
PRD / Technical Framing 信息缺失 / 冲突                 → NEEDS_CONTEXT
环境、依赖、权限、外部因素阻塞实现或验证                 → BLOCKED
```

DONE_WITH_CONCERNS 的前提是**功能代码已兑现 PRD 承诺**，只是某些路径没法在当前环境完整验证。若实际交付物与 PRD 承诺不一致（典型如用替代方案顶替承重决策），按 anti-patterns "静默做设计决策以解除阻塞" 处理：停下报 NEEDS_CONTEXT。每条 concern 写 "PRD 完成标志原意 vs 实际实现"。

## 记录结果

```bash
sdd-arbor record-impl-result <package> \
  --state done|done_with_concerns|needs_context|blocked \
  --summary "<一句话总览本次 impl 范围>" \
  --acceptance "<marker-id>: <证据>"  \
  --command "<self-check 命令>" \
  --concern "<PRD 原意 vs 实际>" \
  ...
```

`--acceptance` / `--command` / `--concern` 可重复。

**Acceptance 引用格式**——helper 会校验覆盖：

- slice 只有 1 个"完成标志"（单行写法）→ 用 `S-NNN: <证据>`。
- slice 有多个"完成标志"（sublist 写法）→ 每个 marker 单独一条 `S-NNN.M: <证据>`。漏了任何一条 helper 会拒绝 `--state done`；接受妥协就改 `--state done_with_concerns` + `--concern`。

例：

```
--acceptance "S-001: GET /api/courses 返回 2 条种子 + e2e 通过"
--acceptance "S-004.1: 代报名 API + UI form 走通"
--acceptance "S-004.2: 取消 API + status=cancelled 落库"
--acceptance "S-004.3: 活动详情页展示报名台账"
--acceptance "S-004.4: 重复报名返回 409 + UI 显示错误"
```

若本次 diff 触及 PRD 引用的 wiki cross-cut 页面，或发现"同类改动在多个模块同步修改"的重复模式，record 时提醒用户是否更新 wiki。

## References

- Testing strategy 档位与 TDD loop 见 [`references/tdd.md`](references/tdd.md)。
- 反模式见 [`references/anti-patterns.md`](references/anti-patterns.md)。
- 状态机与 workflow 细节见 [`references/state-machine.md`](references/state-machine.md) / [`references/workflow.md`](references/workflow.md)。
