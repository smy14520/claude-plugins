---
name: team-auto
description: "仅当用户显式说 Team Auto、agent team、多 agent、开 team、辩论、双推、review panel、shadow review 或要求多个 agent 协作时使用。自然语言触发；不是 workflow 阶段，不自动推进 research/brainstorm/impl/review。"
---

# Team Auto — session orchestration

使用语言：中文。

Team Auto 只负责当前会话的多 agent 编排：判断是否需要 Team、选择协作形态、生成 worker role contract、在用户确认后启动并收口。它不是 workflow stage，不写 `.arbor` runtime state，不替代 `research` / `brainstorm` / `impl` / `review`。

## 入口

只有用户明确表达 Team Auto / Agent Team / 多 agent / 开 team / 双推 / 辩论 / panel / shadow review / 每个 slice 后独立审查等协作意图时进入。用户只是说“快一点”“多看看”时，不自动开 Team。

普通 workflow 入口保持普通节奏：

```text
impl 负责实现 PRD scope + required checks。
review 负责审 PRD + diff + check evidence。
Team Auto 只改变协作方式和审查节奏，不改变 DONE / APPROVED 标准。
```

## 默认流程

1. **轻量 context check**：先读当前 package / diff / 用户输入中足以判断协作形态的信息，不做完整 stage 工作。
2. **判断 subagent vs Agent Team**：
   - isolated search / isolated review / 一次性结果回传 → 优先 subagent 或主会话直接做。
   - 需要持续沟通、共享任务状态、互相挑战、角色协商、并行写入协调 → 用 Agent Team。
3. **给 2–4 个本次定制选项**：除非用户已明确指定阵型或说“直接开 / 你决定”，否则用 `AskUserQuestion`，推荐项放第一。
4. **用户确认后启动**：创建 Team、分派 worker、说明写入 owner、可修改范围、required evidence。
5. **收口映射回阶段出口**：Team 的结果必须回到当前 workflow 的出口，例如 brainstorm PRD 决策、impl evidence、review verdict。

## 协作形态来源

`references/formations.md` 是素材库，不是固定菜单。按当前任务改名、裁剪或组合，不要原样倾倒全部阵型。

阶段推荐见 `references/usage-patterns.md`。worker prompt 使用 `references/role-contract.md`，优先写职责契约，不写空泛人设。

## Debate / challenge 要求

凡是称为 debate、双推、架构辩论或共识的 Team，必须有 peer exchange：

1. 立场轮：每个 worker 给出 claim、证据、风险和反对对象。
2. 交叉轮：把核心 claim 发给对立 worker，要求指出哪里错、哪里过度、哪里漏证据。
3. 收敛轮：每个 worker 说明是否修改立场；未收敛分歧要保留。

没有互相挑战，只能称为并行审查或 fan-out，不能称为 debate。

## Slice-gated cadence

如果用户要求“每个 slice 后独立审查”，Team Auto 只负责节奏：

```text
lead 分配一个 slice → impl worker 完成并产出 check evidence → reviewer 按 review 规则审 required_checks / checks / diff → pass 后进入下一个 slice
```

reviewer 审什么、怎么判 pass/rework 归 `review` skill；impl 怎么产生 evidence 归 `impl` skill。Team Auto 不重新定义质量规则。

## 边界

- 不自动创建 Team，除非用户明确授权。
- 不写 `.arbor` control state，不 claim package，不自动进入下一阶段。
- 不默认 worktree；只有写入冲突、候选实现隔离或用户要求时才建议。
- 不自动 commit / push。
- 同一个 durable artifact 只能有一个写入 owner。
- 跨 package 缺口回 lead 判断，不直接 patch sibling internals。

## 收口模板

```text
独立意见：...
互相挑战后改变了什么：...
仍未收敛的分歧：...
采纳：...
不采纳：...
最终结论：<verdict / next_action / handoff>
后续动作：...
```
