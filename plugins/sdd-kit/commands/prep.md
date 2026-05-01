---
description: "Batch prepare an sdd-kit map initiative by resolving package brainstorm/task/freeze work before implementation."
argument-hint: "<initiative> [--grill-me]"
---

# Prep — initiative preparation command

使用语言：中文。

这是显式 slash command，只在用户调用 `/sdd-kit:prep` 时运行。目标是把一个 map initiative 下所有需要人参与的 `brainstorm` / `task` 准备批量做完；不写实现代码，不做 review。

输入来自 `$ARGUMENTS`。如果没有给 initiative，只能在当前 `.arbor/maps/` 中唯一可判断时自动使用；否则先问用户确认。

## State first

先读取当前状态，不要凭记忆猜：

```bash
sdd-arbor map-check <initiative> --json
sdd-arbor validate --all --json
```

必要时读取 `.arbor/maps/<initiative>/map.md` / `map.json`，以及相关 package 的 `prd.md` / `task.md` / `task.json`。`.wiki` 只能作 orientation，定稿前回到代码或 `.arbor` 验证。

## 分桶

先给出简短准备状态：

- 需要 package brainstorm / PRD 确认的 package。
- PRD 已 ready 但 task 未拆或不完整的 package。
- task 已拆但 definition 未 frozen / validate 失败的 package。
- 被 dependency / contract blocker 阻塞的 package。
- 已 frozen、可进入 implementation queue 的 package。

## 批量准备循环

按这个顺序集中处理问题，避免让用户在 package 间反复来回跳：

1. initiative-level shared decisions。
2. cross-package contract / dependency gaps。
3. package-local PRD gaps。
4. task decomposition / freeze blockers。

一次只问一个问题；每个问题都给出你的推荐答案、理由和影响哪些 package。能从 repo / `.arbor` 确认的事实先查证，不问用户。

对每个 package 复用既有阶段语义：

- PRD / package boundary 属于 `brainstorm` 语义。
- T-xxx 拆解、context 写入和 `freeze-definition` 属于 `task` 语义。
- 机械状态写入必须用 `sdd-arbor` helper；不要手写 `task.json` / `context/*.jsonl`。
- 跨 package 缺口用 contract request 表达；不要直接 patch sibling internals。

如果 `$ARGUMENTS` 包含 `--grill-me` 或用户说 `grill me`：沿 initiative/package graph 追问共享架构、source of truth、contract、验收、权限/状态一致性和风险，直到足以冻结；仍然不进入实现。

## Exit

完成一轮准备后再次运行：

```bash
sdd-arbor map-check <initiative> --json
sdd-arbor validate --all --json
```

输出：

- prepared / frozen packages。
- implementation queue：可进入 `impl` 或 `review` 的 package/task。
- blockers：阻塞原因、owner、建议下一步。
- 如果所有可准备 package 已 frozen，提示用户可以显式运行 `/sdd-kit:run <initiative> --autonomous`。
