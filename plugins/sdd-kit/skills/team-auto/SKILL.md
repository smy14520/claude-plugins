---
name: team-auto
description: "仅当用户显式说 Team Auto、agent team、多 agent、开 team、辩论、双推、review panel、shadow review 或要求多个 agent 协作时使用。自然语言触发；不是 workflow 阶段，不自动推进 research/brainstorm/map/task/impl/review。"
---

# Team Auto — Session-layer Agent Team Playbook

使用语言：中文。

Team Auto 是 sdd-kit 的会话层协作 skill：当用户显式要求 Team Auto / Agent Team / 多 agent 协作时，帮助当前会话选择合适阵型、生成 worker 任务，并在用户确认后启动 Team。

它不是 workflow stage，不写 `.arbor` runtime state，不自动推进阶段，不替代 `research` / `brainstorm` / `map` / `task` / `impl` / `review`。

## 入口

用户可能这样触发：

```text
这个 brainstorm 用 Team Auto
这个 impl 用 Team Auto 提速
这个 review 开多 agent 看看
用 agent team 辩一下这个需求边界
这个需求双推一下，一个激进一个保守
```

如果用户只是泛泛说“能不能更快 / 多看看”，不要自动调用；必须有明确 Team Auto / Agent Team / 多 agent / 开 team / 双推 / 辩论 / panel 等协作意图。

## 默认动作

先做轻量 context check，再给选项：能从当前 repo / diff / package / 用户输入判断的信息先自行查证，不要在不了解当前任务形态时套固定菜单。比如 review 场景应先看目标和 diff 形态；brainstorm 场景应先看用户 plan / repo 相关事实；impl 场景应先看 task/package 和可能的写入边界。

除非用户明确说“直接开 / 你决定 / 如果值得就启动”，否则必须用 `AskUserQuestion` 给 2–4 个**本次定制**的阵型选项，并推荐一个。推荐项放第一，label 简短，description 写清：基于当前观察为什么适合 / 产出 / 成本。

`AskUserQuestion` 示例：

- question: `这次 Team Auto 采用哪个阵型？`
- header: `阵型`
- options:
  1. `<阵型名>（推荐）` — `<为什么适合 / 产出 / 成本>`
  2. `<阵型名>` — `<为什么适合 / 产出 / 成本>`
  3. `主会话直接做` — `<为什么也可行>`

不要只输出文字列表让用户手打选择。

用户选定后，再创建 Team、拆 worker prompt、分派任务。需要写代码或修改状态时，主会话负责确认写入边界。

## 阵型来源

`references/formations.md` 是素材库，不是固定菜单。按当前任务从中选择、改名、裁剪或组合：

- 辩论会 / Debate Council
- 双推 / Dual-track Push
- Role-lane Parallel
- Shadow Review
- Review Panel
- Research Swarm

不要机械列全，不要每次照搬同一组阵型；只给本次最可能有价值的 2–4 个，并允许生成更贴合当前任务的新名字。

## Worker prompt

给 teammate 的提示词优先写 role contract，不写空泛人设。模板见 `references/role-contract.md`。

## 边界

- 不自动创建 Team；除非用户明确授权。
- 不写 `.arbor` control state，不 claim package，不自动进入下一阶段。
- 不默认 worktree；只有写入会冲突、候选实现需要隔离或用户要求时才建议。
- 不自动 commit / push。
- 同一个 durable artifact 只能有一个写入 owner。
- 跨 package 缺口回 lead 判断，不直接 patch sibling internals。
- subagent 适合 isolated result；Agent Team 适合需要持续沟通、共享任务状态或互相挑战的协作。

## 收口

Team 完成后，主会话汇总：

```text
共识：...
分歧：...
采纳：...
不采纳：...
后续动作：...
```
