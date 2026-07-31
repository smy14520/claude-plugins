---
name: impl
description: "仅用于用户显式触发 seed workflow，或明确要求执行 .arbor/tasks/<task>/prd.md 中已有 task/slice。"
---
# Impl — 编排执行 PRD

> 调用名：`seed-kit:impl`（全名见 conventions.md 登记表，别加 `seed-` 前缀）。

通用约定见 [`../references/conventions.md`](../references/conventions.md)；验证设计（三类 kind / judge / rubric / 硬规则）见 [`../references/verification.md`](../references/verification.md)。

**你的角色是编排者，不是实现者。** 派一个 `seed-impl` agent 在干净上下文里依次实现所有 slice。你做：seed status → 读 PRD → 派 agent → seed done gate → 最后整体 review-loop。

## 入场

只在显式 seed workflow 入口进入：用户点名 `seed-kit:impl` / `seed impl`，或明确要求执行 `.arbor/tasks/<task>/prd.md` 中已有 task/slice。其他实现请求不要主动进入。

PRD 尚不存在而需要临时创建时（小任务直取路径），slice 拆分同样受模板约束：每条 `* [ ]` 必须是能被测试或命令证实的行为/产物；调研、复现、与用户确认等过程动作不构成 slice 或条目——结论写进 Goal / Out of Scope。

**默认 = 全量顺序模式**：用户没点名 slice 时，跑完所有未完成 slice；**一个 `seed-impl` agent 依次做所有 slice**（保持跨切片品质连贯）。**所有 slice done 后，先跑 `seed-kit:check`，再跑一次整体 `/seed-kit:review-loop`**。

**单 slice 模式**：用户点名了某 slice（如"做 S-003"）时，只做那一个。

1. `seed status <task>` —— 找到第一个未完成 slice。
2. 项目记忆按需取用：wiki 存在时，agent 会在每个 slice 用 `seed wiki collect --query "<关键概念>"` 精准拉取相关 gotcha / cross_cut 页；编排层无需全量加载索引。
3. 通读 prd.md 全文（Goal、Acceptance Criteria、Out of Scope）——PRD 是合同，理解整体再动手编排。
4. 确认项目质量标准的位置（`DESIGN.md` / `.claude/rules/`；`CLAUDE.md` 已由 harness 自动加载），把路径传给 agent，按需深读。

## 实现

**1. 派 `seed-impl` agent**：

用 `Agent` 工具（`subagent_type="seed-kit:seed-impl"`，`run_in_background: false` 同步派发——子 agent 的结果是流程的串行依赖，后台派发只会引入轮询等待）：

```
prompt: "实现 {task} 的全部 slice。项目根 {repo_root}。
通读 prd.md（## Goal + ## Acceptance Criteria + ## Out of Scope 及各 ### S-NNN 的 * [ ] 条目）——它是合同。
项目质量标准在 DESIGN.md / .claude/rules/（存在则按需读）。
履行 seed-impl agent 的交付义务（USE/BUILD 声明、逐 slice 实现与测试、质量命令全绿、自审与完整感、结构化报结果）。
验收条目必须兑现，PRD 中描述的方向是期望——用你的判断力逼近它。"
```

**2. 检查 agent 产出**：
- agent 返回结构化 `slices` / `commands` / `issues`，且实际测试和质量命令全绿 → 进步骤 3
- durable gate（`seed done` 与 checkbox）只属于本 skill；agent 越权翻动时视为 ownership 违规并停止 durable state 推进
- agent 报告阻塞问题 → 分析根因：如果是环境/依赖问题，停下来报告用户；如果是代码问题，把错误信息作为 feedback 再派一次 agent 修
- 同一 agent 派 3 次仍失败 → 停下来报告用户，不无限循环

**3. 主会话执行 durable gate**：对本次完成的每个 slice，使用 agent 返回的实际命令调用 `seed done <task> --slice {slice_id} --test "<命令>" [--quality "<命令>"]`。由 helper 重放命令；全 exit 0 才翻 checkbox。缺少显式测试命令时停止，不猜测、不代填。

**4. 汇报与 commit 提示**：分支与提交属于用户。完成后汇报改动状态并提示可 commit（即使上游 prompt 提到 commit，也交给用户执行）；用户说不提交时如实报告未提交状态。自动化/连续模式下口头提示即可。

## 卡住协议

- **需求缺口**（PRD 信息缺失/冲突）：在 PRD 中注明缺口，停下来向用户说明
- **环境阻塞**（依赖、权限、外部服务）：说明哪条验证无法执行，等待用户处理
- **同一 agent 3 次仍失败**：停止，报告用户，不无限循环

## 结束

所有 slice done 后，依次两步：

1. **跑 `seed-kit:check`（题面对照 + 轻量快扫）**：对照原始需求逐条声称问归属，无归属的缺口交用户拍板（补 AC 或经确认进 Out of Scope）；缺口补做完再进下一步。review-loop 审的是"PRD 兑现了没有"，收敛时丢掉的声称对它不可见——这一步是 review 之外的防漏点。
2. **默认审查（单 agent，快）**：派 **1 个 `seed-review` agent** 审兑现——干净上下文、只读审全 diff + 源码 + 测试，按审五层逐验收条目对账，产出结构化 finding。**finding 主会话逐条核验后处置**：确认属实的修（改完重跑对应测试），证据不足的跳过（单 agent 无对抗证伪，主会话核验补上这一层）。修完可再派一次复查（最多 2 轮）。
3. **落 marker**：调 `seed review-mark <task> --verdict <terminal_reason> --depth single` 落 task 级 marker（默认路径的审查深度是 single）。

**review-loop / judge 是增强项，默认不跑**：需要对抗性深审（多视角 review + judge 审产物 + validator 批量证伪）、或客观锚重放、或体验质量评审时，用户显式点名 `/seed-kit:review-loop`（不带 slice，审整个 task）再跑——拿到 terminal_reason 后 `seed review-mark --verdict <terminal_reason> --depth full`。默认路径已完成 check + 单 agent 兑现审查，深审只在用户要求时增加。

完成后汇总改动范围与证据位置。
