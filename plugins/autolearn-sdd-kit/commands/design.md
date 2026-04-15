---
name: design
description: 调用架构师进行方案设计
argument-hint: "[需求描述]"
allowed-tools: "Read, Write, Glob, Grep, Task"
model: sonnet
---

你正在执行 `autolearn-sdd-kit` 插件命令 `/autolearn-sdd-kit:design`。

用户需求：`$ARGUMENTS`

如果没有提供需求描述，直接输出以下用法后结束：

```text
/autolearn-sdd-kit:design <需求描述>
```

这条命令的目标，是为当前项目生成设计方案文件：`.claude/plans/<需求名>-plan.md`。对当前项目 `.claude/plans/**` 的写入属于本命令的预期输出，不要为这些项目内、本地、可逆写入再次请求确认。

## 执行要求

1. 优先读取已有项目知识资产，而不是先全仓扫描：
   - `.claude/modules/INDEX.md`
   - 与需求最相关的模块索引（如 `auth-index.md`、`notes-index.md`）
   - 一跳相关源码与测试
2. 如果需求本身是在优化**插件/命令/交互体验**，优先读取：
   - `README.md`
   - `REAL_SESSION_VALIDATION.md`
   - 直接相关的 `commands/*.md` / `agents/*.md`
   不要先扫业务代码。
3. 除非已有索引、文档和一跳源码明显不足，否则不要先做 `src/**/*` 级别的大范围搜索。
4. 如果需求小且上下文已经足够清楚，可以直接设计；如果需求存在明显歧义、跨模块较多、或需要方案对比，优先启动 `autolearn-sdd-kit:Architect` agent 完成设计。
5. 只有在确实缺信息时才提问，而且一次只问一个问题；如果已有足够信息，不要为了流程而提问。
6. 必须比较 2–3 个可行方案，并明确推荐一个。
7. 设计方案必须落到当前项目真实结构上，不要写脱离代码库的通用模板文档。
8. 把最终设计写入 `.claude/plans/<需求名>-plan.md`。
9. 完成后输出：
   - 设计文件路径
   - 推荐下一步：`/autolearn-sdd-kit:tasks <需求名>`

## 设计文档最低要求

最终文档至少包含：
- 背景与目标
- 方案对比与推荐
- 技术设计
- 边界与约束
- 风险与建议
