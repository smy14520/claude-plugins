---
name: impl
description: "仅用于用户显式触发 seed workflow，或明确要求执行 .arbor/tasks/<task>/prd.md 中已有 task/slice。"
---
# Impl — 编排执行 PRD

> 调用名：`seed-kit:impl`（全名见 conventions.md 登记表，别加 `seed-` 前缀）。

通用约定见 [`../references/conventions.md`](../references/conventions.md)；验证设计（三类 kind / judge / rubric / 硬规则）见 [`../references/verification.md`](../references/verification.md)。

**你的角色是编排者，不是实现者。** 派一个 `seed-impl` agent 在干净上下文里依次实现所有 slice。你做：seed status → 读 PRD → 派 agent → seed done gate → 收尾自查（题面对照 + 兑现对账，内联）→ review-mark。

## 入场

只在显式 seed workflow 入口进入：用户点名 `seed-kit:impl` / `seed impl`，或明确要求执行 `.arbor/tasks/<task>/prd.md` 中已有 task/slice。其他实现请求不要主动进入。

PRD 尚不存在而需要临时创建时（小任务直取路径），slice 拆分同样受模板约束：每条 `* [ ]` 必须是能被测试或命令证实的行为/产物；调研、复现、与用户确认等过程动作不构成 slice 或条目——结论写进 Goal / Out of Scope。

**默认 = 全量顺序模式**：用户没点名 slice 时，跑完所有未完成 slice；**一个 `seed-impl` agent 依次做所有 slice**（保持跨切片品质连贯）。**所有 slice done 后，进入收尾自查（题面对照 + 兑现对账 + marker，详见「结束」节）**。

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

所有 slice done 后，收尾自查——你自己做，不派 agent。**用全新的视角复审产出，重点找可能写错的地方**；整个自查闭环（发现问题→修→重验→落 marker）自动推进，不停下来请示——只有缺口拍板和 commit 归用户。独立深审（seed-review / review-loop）不在闭环内自动派，由用户点名。

**1. 题面对照**：按 `seed-kit:check` 的清单内联执行（不 dispatch 该 skill）——对照原始需求（不是 prd.md）逐条声称问归属：某条 `* [ ]` 条目、Out of Scope（用户确认），或缺口。缺口交用户拍板（补 AC 走补做，或经确认进 Out of Scope），不单方排除；顺带做一轮轻量质量快扫。review-loop 审的是"PRD 兑现了没有"，收敛时丢掉的声称对它不可见——这一步是 review 之外的防漏点。

**2. 兑现对账**：读 `git diff` 与源码，逐条验收条目对账实现位置(file:line)与测试覆盖；**把你依赖的关键假设显式列出来**（接口语义、边界条件、并发前提——写出来，别只在脑子里）。发现漏条目、缺测试、机械问题直接修，改完重跑对应测试。

**3. 准则对照**：按 `seed-kit:check` 清单的职责三执行——读项目质量标准（CLAUDE.md / DESIGN.md / .claude/rules/；改动触及插件自身时含该插件的 CLAUDE.md），对照本次 diff 触及的准则逐条检查是否遵守，产出 遵守/违反 结论与证据（file:line + 准则原文）。实现层违反直接修（改完重跑对应测试）；准则本身冲突或需改 → 报告用户拍板，不单方定。

深度由你判断：简单任务快扫即过，复杂任务逐条细对。自查有抓不到的**盲点**（实现者写代码时带进去的假设）。**独立深审不在收尾自动派**——默认内联自查即收尾，不因“不放心”自动升级（升级常空转，实测有连派 2 次均无 finding）。需要独立视角时**由用户显式点名**：派 `seed-review` 在**干净 context** 审某段，或 `/seed-kit:review-loop` 审整个 task；用户没要求就不派。

**4. 落 marker（必做）**：自查收敛后 `seed review-mark <task> --verdict converged --depth inline`（用户点名派过 seed-review 时 `--depth single`）。**实现层 blocking**（AC 没兑现 / 没测试 / 偷懒签名 / 测试挂）在兑现对账那步直接修，不停；**只有决策层 blocking 修不掉时才不落 converged、停下报告用户**——题面缺口未拍板、AC 歧义、修了会动 scope 或契约、AC 本身错——这些你无权单方定。

**review-loop / judge 是增强项，默认不跑**：需要对抗性深审（多视角 review + judge 审产物 + validator 批量证伪）、或客观锚重放、或体验质量评审时，用户显式点名 `/seed-kit:review-loop`（不带 slice，审整个 task）再跑——拿到 terminal_reason 后 `seed review-mark --verdict <terminal_reason> --depth full`。

完成后汇总改动范围、证据位置与关键假设清单。
