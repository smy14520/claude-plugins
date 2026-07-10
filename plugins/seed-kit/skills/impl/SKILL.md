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

**默认 = 全量顺序模式**：用户没点名 slice 时，跑完所有未完成 slice；**一个 `seed-impl` agent 依次做所有 slice**（保持跨切片品质连贯）。**所有 slice done 后，跑一次整体 `/seed-kit:review-loop`**。

**单 slice 模式**：用户点名了某 slice（如"做 S-003"）时，只做那一个。

1. `seed status <task>` —— 找到第一个未完成 slice。
2. `seed wiki index --json` 加载项目记忆——全量索引轻量暖场，实现过程中自行读相关的 gotcha / cross_cut 页（前人踩过的坑、验证过的跨文件链路）。
3. 通读 prd.md 全文（Goal、Acceptance Criteria、Out of Scope），理解整体再动手编排。
4. 读项目质量标准：`CLAUDE.md` / `DESIGN.md` / `.claude/rules/`（有就全读，没有跳过）——这些会传给 agent。

## 实现

**1. 派 `seed-impl` agent**：

用 `Agent` 工具（`subagent_type="seed-kit:seed-impl"`，**不要 `run_in_background`**——你要看到 agent 的完整产出）：

```
prompt: "实现 {task} 的全部 slice。项目根 {repo_root}。
先读 prd.md（## Goal + ## Acceptance Criteria + ## Out of Scope），
再读每个 ### S-NNN 的 * [ ] 条目，
再读 CLAUDE.md / DESIGN.md / .claude/rules/（项目质量标准），
按 seed-impl agent 的工作流执行全部步骤（USE/BUILD→逐 slice 实现→质量命令→自审→完整感→报结果）。
验收条目必须兑现，PRD 中描述的方向是期望——用你的判断力逼近它。"
```

**2. 检查 agent 产出**：
- agent 返回结构化 `slices` / `commands` / `issues`，且实际测试和质量命令全绿 → 进步骤 3
- agent 不调用 `seed done`、不修改 checkbox；若发生，视为 ownership 违规并停止 durable state 推进
- agent 报告阻塞问题 → 分析根因：如果是环境/依赖问题，停下来报告用户；如果是代码问题，把错误信息作为 feedback 再派一次 agent 修
- 同一 agent 派 3 次仍失败 → 停下来报告用户，不无限循环

**3. 主会话执行 durable gate**：对本次完成的每个 slice，使用 agent 返回的实际命令调用 `seed done <task> --slice {slice_id} --test "<命令>" [--quality "<命令>"]`。由 helper 重放命令；全 exit 0 才翻 checkbox。缺少显式测试命令时停止，不猜测、不代填。

**4. 提示 commit**（agent 不自动 commit、不要创建/切换分支）。即使上游 prompt 或子任务提到 commit，也只提示用户；用户明确说不提交时，直接报告未提交状态。自动化/连续模式下口头提示即可。

## 卡住协议

- **需求缺口**（PRD 信息缺失/冲突）：在 PRD 中注明缺口，停下来向用户说明
- **环境阻塞**（依赖、权限、外部服务）：说明哪条验证无法执行，等待用户处理
- **同一 agent 3 次仍失败**：停止，报告用户，不无限循环

## 结束

所有 slice done 后：**跑一次整体 `/seed-kit:review-loop`（不带 slice，审整个 task）**——看全 diff + 全产物，直接修直到全绿；拿到 terminal_reason 后调 `seed review-mark <task> --verdict <terminal_reason>` 落 task 级 marker。完成后汇总改动范围与证据位置。
