# Team Auto formations

这些是素材库，不是固定菜单。Team Auto 应先观察当前任务形态，再按需增删、改名、组合或生成更贴切的新阵型；默认只给用户 2–4 个选项。

## 辩论会 / Debate Council

适合：research、brainstorm、架构不确定、需求边界不清。

做法：多个 agent 从不同立场互相挑战假设，目标是暴露薄弱点，而不是快速达成表面共识。

常见角色：

- product skeptic：压目标、非目标、用户流、验收口径。
- tech lead：压架构、状态、数据、测试和集成风险。
- scope cutter：压 MVP、非目标和回滚边界。
- domain critic：压业务规则、权限、交易、内容或玩法边界。

产出：共识、分歧、被推翻的假设、最高价值追问、推荐下一步。

## 双推 / Dual-track Push

适合：impl 前方案竞争、同一需求有两条合理路线、用户想比较激进/保守实现。

做法：leader 派两个执行者沿不同策略推进，最后比较并吸收优点。不是机械二选一。

常见组合：

- 保守派 vs 激进派。
- 架构派 vs 快速实现派。
- 最小改动 vs 长期可维护方案。
- UI-first vs data/model-first。

产出：两个路线的实现/方案摘要、取舍、可吸收点、最终推荐。

## Role-lane Parallel

适合：单个 package 内天然按职责分工，例如前端 / 后端 / 测试 / 美术 / 文档 / devops。

做法：lead 先确认 shared/contract 任务、依赖顺序和文件/资产 ownership；每个执行者在自己的 lane 内串行处理一组 T-xxx。

默认不要求 worktree；只有写入重叠、候选实现隔离或用户明确要求时才建议。

产出：每个 lane 的变更、已跑验证、剩余风险、需要 lead 决策的 cross-lane 问题。

## Shadow Review

适合：实现路线清楚，但质量、边界、项目公约或安全风险较高。

做法：一个 agent 正常推进，另一个 shadow agent 同步审视风险、提出阻塞问题或审查 diff。shadow 不直接改代码，除非 lead 明确授权。

产出：实现结果 + shadow 风险清单 / 必修问题 / 可接受 notes。

## Review Panel

适合：review、大 diff、workflow/helper/skill 改动、需要多角度审计。

做法：多个 reviewer 分别从不同角度审查，再由 lead 汇总。

常见角度：

- 架构 / 边界。
- 代码质量 / 可维护性。
- 测试 / 回归。
- 项目公约：`CLAUDE.md`、`.claude/rules`。
- 安全 / 权限 / 状态一致性。
- 反复杂度 / 少即是多。

产出：阻塞问题、非阻塞 notes、通过点、最终 review 建议。

## Research Swarm

适合：需要多来源、多假设或多代码区域的 research，但最终写入必须由主会话审计。

做法：多个 agent 分头查不同来源/假设/模块；主会话去重、核验证据、决定是否写入 research artifact。

产出：source-backed findings、冲突证据、未验证假设、建议的下一问或下一步。
