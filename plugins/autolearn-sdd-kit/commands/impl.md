---
name: impl
description: 执行实现
argument-hint: "[需求名] [--parallel] [--no-tests]"
allowed-tools: "Read, Edit, Task"
model: sonnet
---

你正在执行 `autolearn-sdd-kit` 插件命令 `/autolearn-sdd-kit:impl`。

用户输入：`$ARGUMENTS`

如果没有提供需求名，直接输出以下用法后结束：

```text
/autolearn-sdd-kit:impl <需求名>
/autolearn-sdd-kit:impl <需求名> --parallel
/autolearn-sdd-kit:impl <需求名> --no-tests
```

这条命令的目标，是按 `.claude/tasks/<需求名>.tasks.md` 执行实现，并在同一文件内维护一个**generated execution snapshot**（如 `## Implementation Record`）。
对当前项目源码与 `.claude/tasks/**` 的必要写入属于本命令的预期输出；这些都是项目内、本地、可逆的改动，不要为此再次请求确认。

## 执行要求

1. 从 `$ARGUMENTS` 中识别：
   - 需求名
   - 是否包含 `--parallel`
   - 是否包含 `--no-tests`
2. 只读取最小必要上下文：
   - `.claude/tasks/<需求名>.tasks.md`
   - 如有必要，再读取 1–2 个直接相关文件
   如果 tasks 文件已足够可执行，不要额外扩展探索。
3. 只允许一次委派：启动 `autolearn-sdd-kit:Developer` agent 执行实现。
4. 外层命令不要再次规划、不要重复解释实现方法、不要再次调用同名 skill / command，也不要在 Developer 返回后做二次实现分析。
5. 外层命令必须把以下契约清楚传给 `Developer`：
   - `TaskCreate` / `TaskUpdate` 仍是本次会话内的运行时真源
   - `.tasks.md` 的**原 Task 正文**仍然是 spec，不得改写为执行日志
   - 只允许在固定 generated section 中同步执行状态；如果 section 不存在，自动插入；如果已存在，只覆盖该区块
6. `--parallel` 的含义是：**请求使用多个 subagent 做安全的 best-effort 并行**，不是保证提速，也不是 Team 模式。
   - 仅当 top-level Task 的 `depends_on` 已满足且 `files` 无重叠/无明显冲突时，才应 fan-out 给多个 subagent
   - 默认不要创建 Team / 不要使用 `TeamCreate`；这里的并行语义是同一轮 dispatch 多个 subagent，而不是建立长期协作团队
   - 如果不存在安全可并行组，必须自动降级为顺序执行
   - 无论是否真正并行，最终都必须明确报告实际模式与降级原因（如有）
7. 外层命令的职责只有三件事：
   - 传递任务文件与 flags 给 `Developer`
   - 接收 `Developer` 的执行结果
   - 输出最短完成摘要
8. 如果 `Developer` 已经给出完整实现结果，外层不要继续“thinking longer”；直接输出以下固定字段：
   - Requested mode（sequential / parallel_requested）
   - Parallel strategy（none / subagents）
   - Actual mode（sequential / parallel_used / parallel_fallback）
   - Fallback reason（如无则省略）
   - Status sync（synced / blocked / skipped）
   - Status file（如有：`.claude/tasks/<需求名>.tasks.md`）
   - 已完成的任务摘要
   - 修改文件列表
   - 如果状态回写被权限或环境拦截，必须如实写 `Status sync: blocked`，不要同时声称“已同步状态文件”
   - 推荐下一步：`/autolearn-sdd-kit:extract-experience <需求名>`
