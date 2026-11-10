---
name: develop
description: "端到端工程交付：判断处境，由你直接调用对应 skill，从想法推进到审查过的改动；只在方案确认与交付两处等人。"
disable-model-invocation: true
---

# Develop

下面是一张从想法到交付的路线图，由你亲自走：需要哪个 skill，就用 Skill 工具调用它。它是地图而不是轨道——每个节点用什么 skill、何时绕行、何时回到主线，按你对这个任务的判断来；路线之外的 skill（`research`、`diagnose`、`codebase-design`……）同样随时可取。

人只在两处介入：**方案确认**与**交付**。路由、阶段切换、上下文管理由你决定；每次转向前用一句话说明判断（"这是 X，我走 Y"），人随时可以打断改道。

## 任务记录

每个任务一个目录 `.forge/<slug>/`（slug 取自参数，或从需求推导的短小写名），与该任务的 spec、tickets 同处。`state.json` 记录对齐结论：原始需求、明确的功能点、agreed seams、out of scope 及理由、关键决策。它是接续与审查的依据；做到哪一步，从盘上的产物（state.json、spec、tickets、git log）读出来。

## 入口：先看处境

- **故障**：描述的是现象、报错或回归 → 调用 `fix`。
- **大而模糊**：一个会话装不下，或决策彼此咬合、看不清先后 → 调用 `wayfinder` 画决策地图。地图清晰后回到主线的 `to-spec` → `to-tickets`，把关联决策收拢成 spec 并拆成垂直切片 tickets；只有事情最终证明很小时才直接 `implement`。
- **小而清楚**：改动一句话说得清，没有真正的分叉 → 直接调用 `implement`。
- **其余**：走主线。

## 主线：想法 → 交付

1. **对齐**：调用 `grill-with-docs`。遇到只有跑起来才答得出的问题（状态模型、业务逻辑、要亲眼看的界面），派 subagent 调用 `prototype` 去回答，把它的 verdict 带回访谈继续。
2. **🛑 方案确认**：访谈收敛后，呈上 agreed seams、out of scope、原始需求逐项对照表（每一项落在哪里），以及工作将提交到的 branch；写入 state.json，等人确认或调整。
3. **实现**：
   - **单会话装得下** → 在当前上下文直接调用 `implement`（在当前工作区与当前分支就地实现，严禁私自创建 worktree）。它收尾的 `tinder-kit:code-review` 以 state.json 的对齐结论为 spec。
   - **多切片 / 多会话** → 调用 `to-spec` 生成 `spec.md`，再调用 `to-tickets` 拆成带 blocking edges 的垂直切片 tickets：
     - **默认按序落地（不建 worktree）**：按 blocking edges 顺序，在当前工作区逐张票派 fresh subagent（或原地按序）调用 `implement`，每完成一张将对应 ticket 置为 `resolved`；
     - **多 worktree 并行**：仅当用户显式要求使用 worktree 并行时，调用 `implement-spec` 在独立的 integration branch 上并行落地全部 tickets。
4. **🛑 交付**：汇报改动内容与修改的文件清单（多会话并行时为 integration branch）、审查结论与测试证据，改动保留在工作区交还控制权（除非用户明确指示，不自动提交）。

## 阶段边界

阶段之间自己判断：默认原地继续；上下文接近 smart zone（约 150k tokens）时，在最近的边界 compact，或把剩余工作交给 subagent。`handoff` 只用于跨目录、换工具或交给同事。
