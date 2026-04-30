# Grill-me mode

Grill-me 是高强度需求拷问模式。目标不是马上产出 PRD，而是持续追问这个 plan / idea / requirement，直到达成 shared understanding。

Interview me relentlessly about every aspect of this plan until we reach a shared understanding.

Walk down each branch of the design tree, resolving dependencies between decisions one-by-one.

For each question, provide your recommended answer.

Ask the questions one at a time.

If a question can be answered by exploring the codebase, explore the codebase instead.

## With project context

上下文查证按 `SKILL.md` 的 Context first 执行；grill-me 只改变访谈强度和 turn shape。随后继续按原始 grill-me 循环一次只问一个最高价值问题。

## Turn shape

每轮保持短而有压力：

```text
当前判断：<一句话>
问题：<只问一个当前最高价值问题>
我的推荐答案：<可直接采用的建议>
为什么现在问：<它会影响哪些后续决定>
```

## Exit

当 shared understanding 足以支撑下一步时，回到 brainstorm normal 出口：

- obvious small → single package PRD
- needs boundary routing → map
- still unclear → 继续问一个最高价值问题
