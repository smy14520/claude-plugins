---
name: brainstorming
description: "Brainstorming — 用于需求不清、需要方案对比或跨模块设计时的显式设计流程。小而明确的修改通常不需要进入该流程。"
argument-hint: "[需求描述]"
allowed-tools: "Read, Write, Glob, Grep, Task"
model: sonnet
---

这是一个设计类薄 orchestrator 命令。

外层命令的职责只有三件事：
1. 判断这次请求是否真的需要 brainstorming
2. 在需要时读取 `skills/brainstorming/SKILL.md` 并按其中流程执行
3. 把最终设计落盘到 `.claude/plans/<需求名>-plan.md`

执行要求：
- 如果只是小而明确的修改，直接提示不需要进入 `/autolearn-sdd-kit:brainstorming`，不要继续做重型探索。
- 如果用户输入已经足够明确，优先直接进入流程，不要先做闲聊式反问。
- 如果流程已经给出完整设计结果，外层不要再做第二轮大范围分析，只做最小整理后落盘。
- 命令内部引用、示例与下一步提示统一使用 namespaced 形式。

如果用户没有提供需求描述，才询问用户想要构建什么。
