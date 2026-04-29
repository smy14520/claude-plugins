---
description: Prompt design principles for plugin and skill authoring in this repository.
---

# Prompt design

本文件是本仓库提示词设计技巧的长期沉淀入口，不隶属于某一个具体原则。后续新增的 prompt/skill 写法、留白技巧、表达模式、反模式和示例，优先追加到这里；只有具体 workflow 执行步骤才放进对应 `SKILL.md`。

## 少即是多

提示词里的“少”不是少表达，而是少做不必要的枚举、禁令和解释。好的提示应该给出清晰方向，并给模型留下合理判断空间。

优先写：

```text
使用语言：中文。
```

不要写成：

```text
表述用中文，代码不用中文，JSON key 不用中文，命令不用中文，技术名词不用中文……
```

原因：前者给出目标，模型通常能自然判断代码、JSON、命令、专有名词应保持原样；后者把常识展开成规则，反而增加噪音和误触发概率。

## 留白不是含糊

可以留白的是模型能根据上下文稳定判断的常识；不能留白的是会影响安全、状态一致性或工作流边界的事实。

适合留白：

- 输出语言和表达风格。
- 技术名词、代码、JSON、命令是否保持原样。
- 简单格式选择。
- 不影响状态的措辞细节。

不适合留白：

- 是否能修改文件。
- 是否能执行 destructive action。
- worker 是否必须进入 worktree。
- package worker 的写权限范围。
- contract/mainline/integration 边界。
- 哪些 helper 会修改 durable `.arbor` state。

## 规则应该写成方向，不是补丁列表

当一个规则需要不断追加例外时，优先重新抽象成更高层的方向。

优先写：

```text
skill 负责流程，arbor helper 负责机械动作，hook 只守底线。
```

不要写成一长串：

```text
skill 不要 copy 文件；skill 不要 patch；skill 不要自己 diff；skill 不要直接写 task.json；skill 不要……
```

如果某个动作应该被稳定执行，优先提供 helper；如果某个动作必须被阻止，再考虑 hook。

## 具体命令优于长篇提醒

如果 lead/worker 需要记住一串机械步骤，不要继续加 prompt 规则；把它做成命令。

例如：

```text
arbor.py import-package-artifacts <package> --from-worktree <worktree_ref>
arbor.py finish-worker <initiative> <package> --assignment-id <id> --from-worktree <worktree_ref>
arbor.py wiki-collect --query "<query>" --limit 5 --json
```

比“不要手工 patch；只复制这些 artifact；不要覆盖 task.json；记得记录 artifact_imports……”更稳定。重复上下文交接也一样：优先做成 dispatch packet / module-summary packet / collect JSON，而不是在 prompt 里反复提醒。

## Skill prompt 要短而有边界

`SKILL.md` 应描述：

- 这个 skill 何时入口。
- 当前阶段的目标。
- 读写哪些 artifact。
- 调用哪些 helper。
- 什么时候停止、交给谁、等待什么。

不要把通用提示词技巧、长期项目原则或可测试 helper 细节全部塞进单个 skill。

## 定义交互循环，而不是堆检查清单

优秀的交互型 skill 不只是告诉模型“要问问题”，而是定义一个可持续推进的循环：以什么强度行动、按什么结构推进、每一步怎么和用户交互、什么时候停止。

可复用要点：

- 用强动词定义行为强度，例如 `stress-test`、`grill`、`interview relentlessly`、`walk down`、`resolve`。
- 给出清晰终点，例如“直到达成共同理解”或“直到每个关键决策都有 owner、依据和后续动作”。
- 指定推进结构，例如“沿决策树逐分支推进”而不是“全面考虑”。
- 一次只处理一个问题，降低用户认知负担。
- 每个问题给出推荐答案，让用户判断/修正，而不是从零构造答案。
- 能从代码、`.arbor` 状态或上下文文件确认的事实先自行查证，不要问用户。

优先写：

```text
使用语言：中文。
持续追问这个设计，直到我们对目标、边界、依赖和验收标准达成共同理解。
沿决策树逐分支推进，先解决会影响后续选择的前置决策。
一次只问一个问题；每个问题都给出你的推荐答案和理由。
如果答案能从仓库或 .arbor 状态中确认，先自行查证，不要询问用户。
```

不要写成：

```text
询问用户需求。
询问用户边界。
询问用户依赖。
询问用户验收标准。
不要一次问太多。
如果需要可以看代码。
```

前者定义了交互循环；后者只是检查清单，模型容易问得散、浅、早停。

## 不要为外部偶发问题膨胀规则

发现问题先判断归属：项目 workflow/helper 的稳定缺口才沉淀规则或 helper；外部环境的一次性干扰（例如 shell 更新提示、临时终端状态、用户本地工具交互）修复环境即可，不要把它包装成 workflow 兜底。

优先问：这是 sdd-kit 应负责的可重复状态问题，还是运行环境刚好打断了本次执行？只有前者值得进入规则、hook 或 helper。

## 面向 AI 的表达要避免过度指定实现

如果目标是让模型做正确判断，给判断标准；不要提前规定所有操作细节。

优先写：

```text
发现跨 package 缺口时，记录 contract request，并停止修改 sibling internals。
```

不要写成多段条件树，除非这些条件确实由 helper 或测试验证。

## 中英混合的默认处理

项目协作和 workflow 输出使用中文。代码、命令、路径、JSON key、schema 字段、API 名称和已有专有名词保持原样。通常只需要写“使用语言：中文”，不需要逐项列出这些例外。
