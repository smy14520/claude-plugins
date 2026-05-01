---
name: rules
description: "Interview the user and recommend a small set of project-level `.claude/rules/*.md` files. Use when the user wants reusable project rules, Claude Code rules, design-quality rules, or asks what rules a project should add."
disable-model-invocation: true
---

# Rules Interview — project rule advisor

使用语言：中文。

目标：通过访谈帮助用户为当前项目生成少量高价值 `.claude/rules/*.md`。这是 opt-in 项目治理辅助，不是 sdd-kit workflow stage，也不写 `.arbor`。

## 原则

- 先理解项目目标、风险和协作偏好，再推荐 rules。
- 不生成可从代码直接推导的结构说明。
- 不把一次性任务、当前实现状态、临时计划或近期 diff 写成 rules。
- rules 应该是长期适用的项目级判断原则。
- 少即是多：优先 1–3 条高价值 rules，避免规则膨胀。
- 写入 `.claude/rules` 前必须预览并获得用户确认。
- 如果目标文件已存在，不覆盖；先询问合并、跳过、改名或只输出建议。

## 访谈方式

1. 先轻量查看现有项目上下文：`CLAUDE.md`、`.claude/rules/*.md`、README 或 manifest/package 文件；只读需要判断规则方向的最小信息。
2. 一次只问一个问题；每次给出你的推荐判断，让用户修正。
3. 能从 repo / CLAUDE.md / 现有 rules 确认的事实先自行查证，不问用户。
4. 至少确认：项目做什么、最不能出错的地方、长期质量偏好、AI 最容易做错的事。
5. 最后输出候选 rules 表格：名称、目的、为什么适合、是否推荐、文件路径。

## 候选类型

这些是启发，不是固定菜单。按项目选择、改名、合并或不生成：

- `design-quality.md`：简单、清晰、可演进；避免 speculative future-proofing 和 anemic quick fix。
- `source-of-truth.md`：数据/状态/配置/业务事实的单一来源与写入边界。
- `state-consistency.md`：状态迁移、幂等、并发、事务、审计和回滚。
- `testing-quality.md`：测试边界、真实集成、不可 mock 的核心语义、验收底线。
- `security-boundary.md`：权限、输入边界、秘密、外部调用和高风险操作。
- `workflow-design.md`：AI workflow/helper/hook 分工与状态边界。
- `prompt-design.md`：提示词少即是多、规则分层和表达习惯。
- `ai-collaboration.md`：多 agent、review panel、handoff 和决策收口。
- `frontend-quality.md`：用户可观察行为、交互验证、视觉与可访问性底线。
- `release-safety.md`：发布、迁移、数据变更、回滚和共享系统风险。

## 输出规则草案

规则文件应该：

- 以方向性判断为主，不堆术语。
- 说明为什么重要，以及如何应用。
- 避免绝对化措辞，除非是安全/权限/source of truth 底线。
- 不记录项目结构、文件路径清单、当前任务或临时状态。

推荐格式：

```md
# <Rule title>

<一句话原则。>

## Why

<为什么这个项目需要它。>

## How to apply

- <判断标准或行为方向。>
- <不要做什么，以及例外。>
```

## 写入

只有用户确认后，才写入 `.claude/rules/<name>.md`。写入前先确认父目录存在；若不存在可创建 `.claude/rules`。不要修改 `CLAUDE.md`，除非用户明确要求。
