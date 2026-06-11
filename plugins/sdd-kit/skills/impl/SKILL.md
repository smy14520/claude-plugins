---
name: impl
description: "Execute one sdd-kit package PRD scope as code changes. Pulls context via sdd-arbor impl-packet, settles each slice through the mark-slice evidence gate, and records DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED."
---
# Impl — execute PRD scope
通用约定见 [`../references/conventions.md`](../references/conventions.md)。
Impl 执行一个 package 的 PRD scope。PRD 是需求 source of truth；进度与证据通过 `sdd-arbor` 结算，gate 不通过的报错会直接给出缺口与出路。
## Hard rules
1. 连续执行所有 slices，不在 slice 之间停顿等待用户确认；只有 NEEDS_CONTEXT / BLOCKED 才停。
2. 信息缺失时停止报 NEEDS_CONTEXT，不靠猜测继续。典型：PRD blocking open questions、Technical Framing 缺承重决定、slice 标注 `[existing]` 资源与实际代码不符、PRD 引用的 `artifacts/` contract 需要改变。
3. 实现聚焦当前 PRD scope；不夹带无关重构、无关抽象或 PRD 外能力。
## 执行循环
1. **入场**：状态非 doing 时先 `sdd-arbor set-status <package> --state doing --actor impl --note "开始执行"`（自动记录 diff 锚点 base_ref，并冻结最新 PRD slices / required checks）。再用 `sdd-arbor impl-packet <package>` 拿入场包（slice 状态、next_slice、read_next）；按 `read_next` 阅读 PRD 承重段、artifacts 与 wiki 页面。`review_result` 为 NEEDS_REWORK 时读问题清单针对性修复，不从头重做。
2. **逐 slice**：`sdd-arbor impl-packet <package> --slice S-NNN` 拿执行包；以 task 文件的 Acceptance 为目标、Approach 为推荐路径实现，并按 PRD Testing strategy 档位补测试（TDD loop 见 [`references/tdd.md`](references/tdd.md)）。
3. **交账**：对该 slice 的 required checks 逐项结算——可自动化的用 `sdd-arbor run-check <package> --required-check <id> -- <command>`；只能人工观察的用 `sdd-arbor record-check <package> --required-check <id> --status passed --evidence "<观察证据>"`；确实无法执行的用 `record-check --status blocked|not_run --reason "<原因>" --evidence "<尝试/错误输出>"`（或 `--command "<尝试命令>"`，gate 会把它结算为 slice concern，包结果导向 DONE_WITH_CONCERNS）。
4. **结算**：`sdd-arbor mark-slice <package> --id S-NNN --status done --acceptance "S-NNN: <证据>"`（多 marker 每条一个 `--acceptance "S-NNN.M: <证据>"`）。未完成用 `--status in_progress --note "<停在哪里>"`。
5. **Functional 验证**：全部 slice 完成后，按 Technical Framing 的 stack / runtime 启动并验证核心路径，并把结果写成 package-level check：自动化用 `sdd-arbor run-check <package> --kind functional -- <command>`；人工观察用 `sdd-arbor record-check <package> --kind functional --status passed --evidence "<核心路径观察证据>"`。Build + Test 通过不等于 DONE；写了测试文件或读代码觉得会过都不是 evidence。
6. **记录**：`sdd-arbor record-impl-result <package> --state <result> --summary "<一句话>" --functional-check <chk_id> [--concern "<PRD 原意 vs 实际>"]`。acceptance / required-check / slice concern 证据自动从已结算 slices 聚合，无需重复提交；存在 slice 级 concern 时 DONE 会被拒绝，改用 done_with_concerns，并写明 concern。
## 结果判定
```
所有 slice 经 gate 结算 + Functional 验证通过                       → DONE
有 required checks blocked/not_run/manual gap + 功能代码已完成      → DONE_WITH_CONCERNS
核心 required checks 无法执行，无法判断核心功能                    → BLOCKED
PRD / Technical Framing 信息缺失 / 冲突                            → NEEDS_CONTEXT
环境、依赖、权限、外部因素阻塞实现或验证                            → BLOCKED
```
DONE_WITH_CONCERNS 的前提是**功能代码已兑现 PRD 承诺**，只是某些路径无法在当前环境完整验证；每条 concern 写 "PRD 完成标志原意 vs 实际实现"。用替代方案顶替承重决策不是 concern，是 NEEDS_CONTEXT。
## Wiki 引用
PRD Technical Framing 引用的 `cross_cut` 页面漏读视为 silent bug：用 `sdd-wiki collect --query "<kw>"` 读取并 verify 位置 / 命名 / 注册机制仍适用；其它类型页面按 orientation 读。本次 diff 触及 cross-cut 页面时，record 时提醒用户是否更新 wiki。
## References
- 判定边界与语义细节见 [`references/state-machine.md`](references/state-machine.md)。
- 反模式见 [`references/anti-patterns.md`](references/anti-patterns.md)。
- TDD 模式见 [`references/tdd.md`](references/tdd.md)。
