---
description: "Run an sdd-kit implementation queue from prepared/frozen packages in a map initiative."
argument-hint: "<initiative> [--autonomous]"
---

# Run — prepared queue command

使用语言：中文。

这是显式 slash command，只在用户调用 `/sdd-kit:run` 时运行。它只消费已经准备好的 package，不替代 `brainstorm` / `task` / `impl` / `review` 的原子语义。

输入来自 `$ARGUMENTS`。如果没有 `--autonomous`，只做只读 queue summary / readiness report，不开始改代码。

## State first

开始前读取当前状态：

```bash
sdd-arbor map-check <initiative> --json
sdd-arbor validate --all --json
```

同时检查当前工作树，避免覆盖用户未说明的改动。发现不熟悉的未提交变更、冲突、缺少依赖、外部凭证或 live 第三方要求时，先停下来说明。

## Readiness gate

只有同时满足这些条件的 package 才能进入执行队列：

- PRD 已 ready。
- task definition 已 frozen。
- `sdd-arbor validate` 通过。
- `map-check` 没有 dependency / contract blocker。
- package `next_action.skill` 是 `impl` 或 `review`。

`run --autonomous` 不补 PRD、不拆 task、不猜需求；遇到准备不充分的 package，记录 blocker 并跳过或停止。

## 执行策略

1. 从 `map-check` 和 package `next_action` 派生当前执行列表；不要创建新的持久队列或运行时状态。
2. 按 dependency/readiness 顺序一次处理一个 package / task。
3. 每完成一个 package/task 后，重新读取 `.arbor` 状态和 readiness；不要假设旧列表仍有效。
4. 处理 `impl` action 时，遵循 `/sdd-kit:impl` 的单 T-xxx 语义：读取 task-local definition，写最小代码变更，运行 acceptance/SelfCheck，使用 `sdd-arbor record-impl-result` 记录结果。
5. 处理 `review` action 时，遵循 `/sdd-kit:review` 的语义审计：审 PRD + task + diff + evidence，使用 `sdd-arbor record-review` 记录结果。
6. 不自动 commit / push / merge；不启动并行执行池；不把 Team Auto 当执行引擎。

## 停止条件

遇到以下任一情况停止 autonomous run，并输出清楚的 next action：

- unclear requirements / missing acceptance / task-local context 冲突。
- validation fail、test fail、acceptance fail。
- contract gap、dependency blocker、跨 package 边界不清。
- `needs_context`、`blocked`、`needs_rework`、`brainstorm_drift`。
- 工作树隔离问题或可能覆盖用户改动。
- 需要真实外部系统、第三方 live 凭证或不可逆操作。

## 输出

结束时输出：

- completed：已实现 / 已审计的 package/task。
- blocked：阻塞项和原因。
- skipped：未满足 readiness gate 的 package。
- next action：最小下一步，通常是回 `/sdd-kit:prep`、单包 `/sdd-kit:task`、单包 `/sdd-kit:impl` 或人工处理 blocker。

不要把部分完成说成全部完成。
