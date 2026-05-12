# Grill-me mode

Grill-me 是高强度需求拷问模式。目标不是马上定稿 PRD，而是持续追问这个 plan / idea / requirement，直到达成 shared understanding。即使在 grill-me 中，也要使用 active PRD draft，并在每轮用户回答后先更新 PRD draft 再问下一个问题。

沿用户场景逐个展开，每个场景追问到触发、行为、成功判定、退化路径和交叉影响都有行为级精度时，才进入下一个。

Follow `SKILL.md` Question interaction rules; grill-me only changes interview intensity and turn shape.

Ask the questions one at a time.

If a question can be answered by exploring the codebase, explore the codebase instead.

## With project context

上下文查证按 `SKILL.md` 的 Context first 执行；grill-me 只改变访谈强度和 turn shape。

存量项目中，grill-me 的追问范围扩展到技术设计决策：

- 产品决策仍然优先（做什么、不做什么、边界在哪）。
- 产品边界基本清楚后，追问关键技术决策：新建表还是扩展现有表？复用现有模式还是引入新模式？怎么和现有模块集成？
- 技术决策同样用 `AskUserQuestion` + 选项的方式确认，附上现有代码分析作为推荐理由。
- 确认的技术决策写入 Technical Framing 和数据备注，具体到表名、关键字段、接口变更。

随后继续按原始 grill-me 循环一次只问一个最高价值问题。

## After research

Research 材料只提供上下文和证据，不代表需求已经被用户确认。

从 research 进入 grill-me 时，第一轮不要直接定稿。先用 research 总结当前判断，并标明哪些仍是假设；然后只问一个会影响 PRD 边界、验收口径、technical framing 的最高价值问题。

不要重复询问已经由用户确认，或由 repo / code / source 明确支持的事实。blocking 问题清零后，整理 PRD（包括 Slices）并按 SKILL.md 的 PRD 定稿条件确认。

## Turn shape

每轮保持短而有压力：

```text
当前场景：<正在展开的场景名>
当前判断：<一句话>
问题：<只问一个当前最高价值问题，交互形式遵守 SKILL.md 的 Question interaction rules>
为什么现在问：<它会影响哪些后续决定>
```

## Exit

当每个场景都已追问到行为级精度、shared understanding 足以支撑下一步时，回到 brainstorm 出口：

- 整理 PRD，写好 Slices，按 SKILL.md 的 PRD 定稿条件确认
- still unclear → 继续问一个最高价值问题
