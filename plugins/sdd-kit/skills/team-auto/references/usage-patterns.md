# Team Auto usage patterns

Team Auto 横跨 sdd-kit 阶段，但不替代任何阶段。它只决定当前会话是否用 Agent Team 协作，以及用什么阵型。

## Brainstorm

常见阵型：辩论会、Research Swarm、Shadow Review。

适合场景：需求边界不清、多个产品方向、架构/业务约束冲突、用户希望“理越辩越明”。

注意：Team 只帮助暴露假设和形成 clarified PRD framing；正式 package PRD 与 `## Slices` 仍由 brainstorm 出口决定。

## Research

常见阵型：Research Swarm、Debate Council。

适合场景：多来源证据、多个代码区域、外部资料和 repo 事实需要交叉验证。

注意：如果只需要 isolated findings，用 subagent 即可。需要多个 agent 持续沟通或互相挑战时，再用 Agent Team。

## Impl

常见阵型：Role-lane Parallel、Dual-track Push、Shadow Review。

适合场景：单个 PRD scope 包含多 role lane；或同一需求存在保守/激进、架构/快速实现两条路线。

注意：默认不使用 worktree。写入范围可能重叠、候选实现需要隔离或用户明确要求时，才建议 worktree。同一个 durable artifact 只能有一个写入 owner。Impl 仍必须按 PRD `## Slices` 连续执行，不让 Team 生成第二套执行计划。

## Review

常见阵型：Review Panel、Shadow Review。

适合场景：大 diff、workflow/helper/skill 改动、安全/权限/状态一致性风险、需要检查项目公约。

注意：review worker 默认只读；最终 review 结论由 lead 汇总，不让多个 reviewer 同时写同一个 durable review artifact。

## Slice / boundary stress-test

常见阵型：Debate Council、Review Panel。

适合场景：PRD `## Slices` 顺序、粒度、scope boundary 有争议，或担心当前 package 过大但又不想恢复拆包复杂度。

注意：Team 只帮助暴露边界风险；正式 PRD、Slices 和 finalize 仍由 brainstorm 收口。若采用 debate/panel，必须让角色互相反驳后再给结论，不能只并行交报告。
