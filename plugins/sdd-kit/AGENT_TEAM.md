# Agent Team Collaboration

Agent Team 是 sdd-kit 的会话层协作能力，不是 workflow 阶段，也不是 runtime。

sdd-kit 不内置 parallel scheduler，也不自动创建 Team。用户可以在任意阶段用自然语言显式要求 Claude Code 使用 Agent Team，例如 brainstorm 辩论、impl 提速、shadow review、双推实现或多角度 review。

## 触发方式

用户可能这样说：

```text
这个 brainstorm 用 Team Auto，先给我几个阵型选项。
```

```text
这个 impl 用 Team Auto 提速，你判断可以怎么开 team。
```

```text
这个 review 开多 agent，从不同角度审。
```

```text
用 Team Auto 处理当前任务。
```

`Team Auto` 不是命令，只表示：用户希望 AI 根据当前任务生成可选 Agent Team 阵型。

## Team Auto

Team Auto 默认不是直接启动 Team，而是先生成 2-4 个本次可用阵型，并推荐一个，让用户选择。

输出要短：

```text
这个任务适合 / 不适合开 Team：<理由>

可选阵型：
1. <阵型名>（推荐）
   <适合原因 / 成本 / 产出>
2. <阵型名>
   <适合原因 / 成本 / 产出>
3. 主会话直接做
   <为什么也可行>

你选哪个？
```

如果用户明确说“直接开 / 你决定 / 如果值得就启动”，才使用推荐阵型直接创建 Team。

## 常用阵型

这些是起手式，不是固定流程。AI 应按当前任务增删、改名或组合。

- **辩论会 / Debate Council**：多个 agent 从不同立场互相挑战，适合 research、brainstorm、架构不确定、需求边界不清。输出共识、分歧、被推翻的假设、最高价值追问。
- **双推 / Dual-track Push**：leader + 两个执行者走不同路线，适合 impl 前方案竞争。常见组合是保守派 vs 激进派、架构派 vs 快速实现派。最后 lead 比较、评分、吸收优点。
- **Shadow Review**：一个 agent 实现，一个 agent 从开始同步审核，适合实现路线明确但质量、边界或项目公约风险较高。
- **Review Panel**：多个 reviewer 从架构、代码质量、测试、项目公约、反复杂度等角度审查，适合 review、大 diff、workflow/helper/skill 改动。

## 边界

- 不创建或维护 `.arbor` runtime state。
- 不自动 claim package，不自动推进 workflow 阶段。
- 不自动 commit / push。
- 不默认修改 PRD、task、rules、CLAUDE.md 或 `.arbor` control state；需要写入时由主会话明确安排。
- 同一个 durable artifact 只能有一个写入 owner。
- 不允许为了方便修改 sibling package internals；跨 package 缺口应记录 contract/request 并回到 lead 判断。
- competing implementation 真写代码时，应使用隔离 worktree 或明确不冲突的文件边界。

## Lead 收口

Team 完成后，主会话输出：

```text
共识：...
分歧：...
采纳：...
不采纳：...
后续动作：...
```
