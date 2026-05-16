# Team Auto usage patterns

Team Auto 横跨 sdd-kit 阶段，但不替代任何阶段。这里是“阶段 → 协作形态”的薄索引；具体质量规则回到对应 skill。

## Brainstorm

推荐形态：Challenge / Debate、Research Swarm、Shadow Review。

适合场景：需求边界不清、多个产品方向、架构/业务约束冲突、用户希望“理越辩越明”。

注意：Team 只帮助暴露假设和形成 clarified framing；正式 package PRD、Technical Framing 与 `## Slices` 仍由 brainstorm 出口决定。

## Research

推荐形态：Research Swarm、Challenge / Debate。

适合场景：多来源证据、多个代码区域、外部资料和 repo 事实需要交叉验证。

注意：只需要 isolated findings 时用 subagent；需要持续沟通、互相挑战或共享任务状态时才用 Agent Team。

## Impl

推荐形态：Role-lane Parallel、Dual-track Push、Shadow Review、Slice-gated Cadence。

适合场景：单个 PRD scope 包含多 role lane；同一需求存在保守/激进路线；多个 slice 无写入冲突可并行；或用户要求每个 slice 后独立 reviewer。

注意：Impl 仍按 PRD `## Slices` 执行，必须产出 required check evidence。Team Auto 可以改变 worker 分工和 review cadence，但不能生成第二套执行计划，不能降低 DONE 标准。

## Review

推荐形态：Review Panel、Shadow Review、Challenge / Debate。

适合场景：大 diff、workflow/helper/skill 改动、安全/权限/状态一致性风险、需要检查项目公约或架构取舍。

注意：review worker 默认只读。最终 review verdict 和 durable review artifact 由 lead 汇总写入，不让多个 reviewer 同时写同一个 artifact。

## Slice / boundary stress-test

推荐形态：Challenge / Debate、Review Panel。

适合场景：PRD `## Slices` 顺序、粒度、scope boundary 有争议，或担心当前 package 过大但又不想恢复拆包复杂度。

注意：Team 只暴露边界风险；正式 PRD、Slices 和 finalize 仍由 brainstorm 收口。采用 debate/panel 时必须让角色互相反驳后再给结论，不能只并行交报告。
