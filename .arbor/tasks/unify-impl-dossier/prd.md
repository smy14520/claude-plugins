# 统一 impl 流程：删除 impl-agent，impl-state 升级为任务档案（dossier）

## Goal

实验 impl-vs-impl-agent-value 判定 impl-agent（per-slice 派发 + per-slice review + 集成 review）质量增益≈噪音（+2.2pp、复评 +1.8pp）而成本结构性上升（token +419%、$ +645%）。本任务删除 impl-agent 双流程，收敛为单一 impl；把 impl-state 从 impl-agent 专属锚点升级为任务通用的**协作档案（dossier）**：锚点（lock-once）+ 每 slice handoff + 验证证据指针——任意新会话/终端读一个文件即可接手任务（痛点句：中断/换终端后，隐性上下文只活在被杀会话的内存里）。设计细节（schema、流程、eval 方案、alternatives）见 [notes/design.md](notes/design.md)。

边界不变量：进度权威仍是 PRD checkbox；验证事实仍在 done-log / gate-attempts（`seed done` 独占写）；dossier 只存协作上下文，被写坏也不能伪造进度。

## Acceptance Criteria

### [x] S-001 删除 impl-agent 双流程

* [x] `skills/impl-agent/SKILL.md` 与 `agents/seed-slice.md` 已删除，全仓库（skills/agents/commands/references/README/DESIGN/docs）无 impl-agent、seed-slice 存活引用
* [x] plugins/seed-kit pytest 全绿

### [x] S-002 dossier 写入机制

* [x] `seed handoff add <task> --slice S-NNN --note "..."` 追加 handoff（重复调用累积；slice 不在 PRD 中则拒绝并报错）
* [x] `seed done <task> --slice S-NNN --test ... [--evidence-file <path>]... [--evidence-url <url>]` 把证据指针写入 impl-state.json 对应 slice（不写 done-log）
* [x] `seed impl-state init` 行为不变：task_start_sha 写一次锁死
* [x] 写序保证：done-log 与 dossier 写入先于 checkbox 翻转（中断不留"已勾选但无证据"状态），有测试证明（制造中途失败，断言 checkbox 未翻而 done-log/dossier 已落）
* [x] test_impl_state.py / test_seed.py 新增用例覆盖上述行为，全绿

### [x] S-003 status 吸收 next-action

* [x] `seed status <task>` 输出含：锚点 SHA、每 slice 的 handoff/evidence 存在性、gate 失败计数（从 gate-attempts/ 现数）
* [x] `seed next-action` 与 `seed impl-state show` 子命令移除，全仓库无存活引用
* [x] pytest 全绿

### [x] S-004 统一 impl 接 dossier

* [x] `agents/seed-impl.md` 返回结构含 `handoffs` 字段（每完成 slice 一组"代码与 git 读不出的隐性事实"）
* [x] `skills/impl/SKILL.md`：入场调 `seed impl-state init`；agent 返回后逐 slice `seed handoff add` 落盘；中断重入说明改为"读 `seed status`（checkbox + 锚点 + handoff + evidence）续接"
* [x] conventions.md 登记表、verification.md、README/DESIGN 的流程叙述同步为单一 impl + dossier

### [x] S-005 eval 认证与结账

* [x] seed-kit-evals-v2 新增场景 `impl-takeover-resume`：任务完成 S-001/S-002 后中断，新会话接管 S-003+；planted 一个只有 handoff 能救的跨 slice 隐式依赖（S-002 做的接口决策，S-003 必须遵守但代码不可见）
* [x] 双臂（treatment=dossier 写入 / control=仅 checkbox+done-log）跑完，`experiments/<id>/CONCLUSION.md` 落盘（结论 + 它打败了什么 + 由此采取的动作）
* [x] `seed review-mark unify-impl-dossier --verdict converged --depth inline`（或按 eval 结果的对应终态）

## Out of Scope

* 不保留 impl-agent 双流程与 per-slice review / 集成 review，依据 impl-vs-impl-agent-value 数据（用户确认）
* 验证证据不进 done-log，进 dossier（用户确认）
* per-slice commit 不保留——统一 impl 交付后由用户一次性提交，commit 归属不变（用户确认）
