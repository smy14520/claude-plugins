# Team Auto formations

这些是协作形态素材库，不是固定菜单。Team Auto 应先看当前任务，再裁剪、改名或组合，只给用户 2–4 个本次最有价值的选项。

Team Auto 决定“谁协作、何时协作、如何通信”；workflow 质量标准仍归对应 stage：brainstorm 定 PRD，impl 产出 required check evidence，review 审 PRD + diff + checks。

## Challenge / Debate

适合：research、brainstorm、架构不确定、需求边界不清、领域模型或 source of truth 有争议。

做法：多个 agent 从不同价值函数挑战假设，目标是暴露薄弱点，而不是快速达成表面共识。必须经过立场轮、交叉反驳轮、收敛轮；如果只是各自交报告，改用 fan-out / subagent，不要称为 debate。

常见角色：

- product skeptic：压目标、非目标、用户流、验收口径。
- scope skeptic：压本次范围、回滚边界、package 是否过大。
- pragmatic architect：压 YAGNI、交付成本、最小可维护边界。
- evolution architect：压 source of truth、invariants、不可逆决策、未来扩展轴。
- domain critic：压业务规则、权限、交易、内容或玩法边界。

产出：初始主张、被反驳后改变的判断、仍未收敛的分歧、当前证据、推荐下一步。

## Dual-track Push

适合：impl 前方案竞争、同一需求有两条合理路线、用户想比较激进/保守实现。

做法：lead 派两个 worker 沿不同策略推进到可比较的方案或小型 spike，最后比较并吸收优点。不是机械二选一，也不是让两个 worker 同时写同一 durable artifact。

常见组合：

- 保守派 vs 激进派。
- 架构派 vs 快速实现派。
- 最小改动 vs 长期可维护方案。
- UI-first vs data/model-first。

产出：两个路线的方案/实现摘要、证据、取舍、可吸收点、最终推荐。

## Role-lane Parallel

适合：单个 package 内天然按职责分工，例如前端 / 后端 / 测试 / 美术 / 文档 / devops。

做法：lead 先确认 shared contract、依赖顺序和文件/资产 ownership；每个 worker 只处理自己的 lane。并行写入范围必须不重叠；有 shared artifact 时指定唯一 owner。

默认不要求 worktree；只有写入重叠、候选实现隔离或用户明确要求时才建议。

产出：每个 lane 的变更、check evidence、剩余风险、需要 lead 决策的 cross-lane 问题。

## Shadow Review

适合：实现路线清楚，但质量、边界、项目公约、安全或状态一致性风险较高。

做法：一个 worker 正常推进，shadow worker 同步只读审视风险、提出阻塞问题或审查 diff。shadow 默认不改代码；如果需要改，必须由 lead 明确授权并限定写入范围。

产出：实现结果 + shadow 风险清单 / 必修问题 / 可接受 notes。

## Review Panel

适合：review、大 diff、workflow/helper/skill 改动、需要多角度审计。

做法：多个 reviewer 分别从不同角度审查，再由 lead 汇总。reviewer 默认只读；最终 durable review artifact 只由 lead 写入。

常见角度：

- 架构 / 边界。
- 代码质量 / 可维护性。
- 测试 / check evidence / 回归。
- 项目公约：`CLAUDE.md`、`.claude/rules`。
- 安全 / 权限 / 状态一致性。
- 反复杂度 / 少即是多。

产出：阻塞问题、非阻塞 notes、通过点、最终 review 建议。

## Slice-gated Cadence

适合：impl 阶段质量要求高、slice 数量多，或用户明确希望每个 slice 完成后有独立上下文 reviewer。

做法：这是审查节奏，不是新的质量标准。

```text
lead 派发一个 slice
→ impl worker 完成该 slice，并产出 required check evidence
→ reviewer worker 按 review skill 审 required_checks / checks / diff
→ lead 根据 pass/rework 决定是否进入下一个 slice
```

Team Auto 只负责何时启动 reviewer、给 reviewer 干净上下文、收集 pass/rework。reviewer 的审查标准来自 `review` skill；check evidence 的产生标准来自 `impl` skill。

产出：每个被 gate 的 slice 的 reviewer 结论、引用的 check id、代码定位证据、返工记录。

## Research Swarm

适合：需要多来源、多假设或多代码区域的 research，但最终写入必须由主会话审计。

做法：多个 agent 分头查不同来源/假设/模块；主会话去重、核验证据、决定是否写入 research artifact。如果 worker 之间不需要互相挑战，优先用 isolated subagent 而不是 Agent Team。

产出：source-backed findings、冲突证据、未验证假设、建议的下一问或下一步。
