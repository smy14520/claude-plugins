# Team Auto usage patterns

Team Auto 横跨 sdd-kit 阶段，但不替代任何阶段。它只决定当前会话是否用 Agent Team 协作，以及用什么阵型。

## Brainstorm

常见阵型：辩论会、Research Swarm、Shadow Review。

适合场景：需求边界不清、多个产品方向、架构/业务约束冲突、用户希望“理越辩越明”。

注意：Team 只帮助暴露假设和形成 clarified framing；是否写 PRD、是否交 map，仍由 brainstorm 出口决定。

## Research

常见阵型：Research Swarm、Debate Council。

适合场景：多来源证据、多个代码区域、外部资料和 repo 事实需要交叉验证。

注意：subagent 也常适合 research；如果只需要 isolated findings，用 subagent 即可。需要多个 agent 持续沟通或互相挑战时，再用 Agent Team。

## Task

常见阵型：Role-lane Planning、Review Panel。

适合场景：单个 package 内有前后端/测试/文档/美术等天然 lane，需要确认并行提示、shared contract 和 ownership。

注意：Team 不拆 `.arbor` task state；task skill 仍负责正式 T-xxx 定义。

## Impl

常见阵型：Role-lane Parallel、Dual-track Push、Shadow Review。

适合场景：单个需求包含多 role lane；或同一需求存在保守/激进、架构/快速实现两条路线。

注意：默认不使用 worktree。写入范围可能重叠、候选实现需要隔离或用户明确要求时，才建议 worktree。

## Review

常见阵型：Review Panel、Shadow Review。

适合场景：大 diff、workflow/helper/skill 改动、安全/权限/状态一致性风险、需要检查项目公约。

注意：review worker 默认只读；最终 review 结论由 lead 汇总，不让多个 reviewer 同时写同一个 durable review artifact。

## Map

常见阵型：Debate Council、Review Panel。

适合场景：package boundary 有争议、single vs split 不清、cross-package contract 风险高。

注意：map 仍只做 boundary routing / package graph，不因为 Team Auto 变成执行器。
