---
name: team-auto
description: "仅当用户显式说 Team Auto、agent team、多 agent、开 team、辩论、双推、review panel、shadow review 或要求多个 agent 协作时使用。自然语言触发；不是 workflow 阶段，不自动推进 research/brainstorm/impl/review。"
---

# Team Auto — session-layer Agent Team playbook

使用语言：中文。

Team Auto 只在用户明确要求多 agent 协作时使用。它帮助当前会话判断是否值得开 Team、选择阵型、生成 worker 任务，并在用户确认后启动 Team。

它不是 workflow stage，不写 `.arbor` runtime state，不替代 `research` / `brainstorm` / `impl` / `review`。Brainstorm 写 PRD；impl 执行 PRD scope；review 审计 PRD + evidence + diff。

## 入口判断

用户可能这样触发：

```text
这个 brainstorm 用 Team Auto
这个 impl 用 Team Auto 提速
这个 review 开多 agent 看看
用 agent team 辩一下这个需求边界
这个需求双推一下，一个激进一个保守
让两个架构师争论一下这个余额模型
```

如果用户只是泛泛说“能不能更快 / 多看看”，不要自动调用；必须有明确 Team Auto / Agent Team / 多 agent / 开 team / 双推 / 辩论 / panel 等协作意图。

## 默认动作

先做轻量 context check：能从当前 repo、diff、package、用户输入判断的信息先自行查证。再判断 Team 是否真的比 subagent 有价值：

- 只是并行收集、读代码、独立审查 → 推荐 subagent 或主会话直接做。
- 需要辩论、互相反驳、角色协商、共享 ownership → 推荐 Agent Team。

除非用户明确说“直接开 / 你决定 / 如果值得就启动”，否则用 `AskUserQuestion` 给 2–4 个本次定制阵型，并推荐一个。不要只输出文字列表让用户手打选择。

用户选定后，再创建 Team、拆 worker prompt、分派任务。需要写代码或修改状态时，主会话负责确认写入边界。

## 辩论型阵型

Debate Council / Architecture Debate Panel / 双推等冲突型阵型必须有 peer exchange：

1. 立场轮：每个 worker 给出 claim、证据、风险和反对对象。
2. 交叉轮：把核心 claim 发给对立 worker，要求指出哪里错、哪里过度、哪里漏证据。
3. 收敛轮：每个 worker 说明是否修改立场；未收敛分歧要保留。

收口时必须能指出“哪一轮争论改变了判断”。没有 peer challenge，就只能称为并行审查，不能称为架构辩论或共识。

## 阵型来源

`references/formations.md` 是素材库，不是固定菜单。按当前任务从中选择、改名、裁剪或组合，只给本次最可能有价值的 2–4 个。

## Worker prompt

给 teammate 的提示词优先写 role contract，不写空泛人设。模板见 `references/role-contract.md`。

## 边界

- 不自动创建 Team；除非用户明确授权。
- 不写 `.arbor` control state，不 claim package，不自动进入下一阶段。
- 不默认 worktree；只有写入会冲突、候选实现需要隔离或用户要求时才建议。
- 不自动 commit / push。
- 同一个 durable artifact 只能有一个写入 owner。
- 跨 package 缺口回 lead 判断，不直接 patch sibling internals。
- subagent 适合 isolated result；Agent Team 只适合需要持续沟通、共享状态或互相挑战的协作。

## 收口

Team 完成后，主会话汇总，并把结论映射回当前阶段出口。辩论型 Team 的汇总必须区分独立意见和经过互相挑战后的结论：

```text
独立意见：...
互相挑战后改变了什么：...
仍未收敛的分歧：...
采纳：...
不采纳：...
最终结论：<verdict / next_action / handoff>
后续动作：...
```
