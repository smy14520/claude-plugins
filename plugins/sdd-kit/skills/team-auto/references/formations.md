# Team Auto formations

这些是素材库，不是固定菜单。Team Auto 应先观察当前任务形态，再按需增删、改名、组合或生成更贴切的新阵型；默认只给用户 2–4 个选项。

## 辩论会 / Debate Council

适合：research、brainstorm、架构不确定、需求边界不清。

做法：多个 agent 从不同立场互相挑战假设，目标是暴露薄弱点，而不是快速达成表面共识。必须至少经过立场轮、交叉反驳轮、收敛轮；如果只是各自交报告，应该改用 subagent fan-out，不要称为 Team debate。

常见角色：

- product skeptic：压目标、非目标、用户流、验收口径。
- tech lead：压架构、状态、数据、测试和集成风险。
- scope skeptic：压本次范围、非目标和回滚边界。
- domain critic：压业务规则、权限、交易、内容或玩法边界。

产出：初始立场、被对方推翻或修正的假设、仍未收敛的分歧、最高价值追问、推荐下一步。

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

做法：lead 先确认 shared/contract、依赖顺序和文件/资产 ownership；每个执行者在自己的 lane 内处理明确的 package scope。

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

## Architecture Debate Panel

适合：需求或 review 涉及领域模型、source of truth、schema/API 取舍、长期演进、抽象边界或核心架构质量；用户想通过争论获得方向和注意事项。

做法：两个 architect 从不同价值函数挑战方案，reviewer/lead 负责追问证据并收口，不以快速达成一致为目标。lead 要把 pragmatic 的主张发给 evolution 反驳，也要把 evolution 的主张发给 pragmatic 反驳；reviewer 负责指出双方哪些主张缺证据、哪些需要写入 PRD。

常见角色：

- pragmatic architect：压 YAGNI、交付成本、最小可维护边界和过度设计风险。
- evolution architect：压领域模型、source of truth、invariants、不可逆决策和未来扩展轴。
- reviewer / lead：核对当前需求证据，区分“当前必须保护”与“可以暂缓”，映射到 PRD / review next_action。

产出：双方初始架构主张、互相反驳后改变的判断、仍未收敛的分歧、当前证据、采纳/暂缓项、建议写入 PRD 的架构意图。

## Slice-gated Review

适合：impl 阶段质量要求高、slice 数量多（6+）、或用户希望每个 slice 完成后有独立视角验证。

做法：impl lead 正常执行 slice；每完成一个 slice 后派一个 reviewer worker 对账该 slice 的 task 文件。reviewer 只看当前 slice，不看全局。

reviewer 对账三件事：

- task 文件 Acceptance 的每条 Then 是否有对应代码产物（文件、函数、路由、UI 元素）。
- Verification 描述的行为是否能观测到（能跑的跑，不能自动化的检查代码路径是否存在）。
- PRD Technical Framing 的承重约束在该 slice 涉及的代码里是否被遵守。

reviewer 返回：pass / 缺口清单（具体到 "Acceptance 第 N 条 Then 缺对应实现"）。

impl lead 收到缺口后补完再继续下一个 slice。如果 reviewer 连续 pass，后续 slice 可以跳过 review（lead 判断）。

产出：每个 slice 的对账结果、累计缺口修复记录、最终 impl 质量置信度。

## Research Swarm

适合：需要多来源、多假设或多代码区域的 research，但最终写入必须由主会话审计。

做法：多个 agent 分头查不同来源/假设/模块；主会话去重、核验证据、决定是否写入 research artifact。

产出：source-backed findings、冲突证据、未验证假设、建议的下一问或下一步。
