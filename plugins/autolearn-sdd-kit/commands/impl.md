---
name: impl
description: 执行实现
argument-hint: "[需求名] [--parallel] [--no-tests]"
allowed-tools: "Read, Task"
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

这条命令的目标，是按 `.claude/tasks/<需求名>.tasks.md` 执行实现。对当前项目源码与 `.claude/**` 的必要写入属于本命令的预期输出；这些都是项目内、本地、可逆的改动，不要为此再次请求确认。

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
5. 外层命令的职责只有三件事：
   - 传递任务文件与 flags 给 `Developer`
   - 接收 `Developer` 的执行结果
   - 输出最短完成摘要
6. 如果 `Developer` 已经给出完整实现结果，外层不要继续“thinking longer”；直接输出：
   - 已完成的任务摘要
   - 修改文件列表
   - 推荐下一步：`/autolearn-sdd-kit:extract-experience <需求名>`
