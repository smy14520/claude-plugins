---
description: Workflow, helper, hook, and state-boundary design principles for this repository.
---

# Workflow design

本文件沉淀 workflow / helper / hook / state 设计原则。它回答“机制应该放在哪里、如何避免规则膨胀、如何保持状态确定”，不记录具体阶段执行步骤；阶段步骤放进对应 `SKILL.md`。

## 机制优于长篇提醒

如果流程需要记住一串机械步骤，不要继续加 prompt 规则；把它做成命令。

例如：

```text
arbor.py add-context-batch <package> --type impl --entry-json '{...}'
arbor.py record-contract-request <initiative> --consumer <package-b> --producer <package-a> --request "..." --status open
arbor.py wiki-collect --query "<query>" --limit 5 --json
```

比“不要手工 patch；不要覆盖 task.json；记得记录 context……”更稳定。重复上下文交接也一样：优先做成 module-summary packet / collect JSON，而不是在 prompt 里反复提醒。

## 先判断问题归属

发现问题先判断归属：项目 workflow/helper 的稳定缺口才沉淀规则或 helper；外部环境的一次性干扰（例如 shell 更新提示、临时终端状态、用户本地工具交互）修复环境即可，不要包装成 workflow 兜底。

优先问：这是 seed-kit 应负责的可重复状态问题，还是运行环境刚好打断了本次执行？只有前者值得进入规则、hook 或 helper。

## 直指系统缺口，而不是局部补丁

遇到 workflow 失败时，先追问“为什么系统会允许这个错误发生”，不要只补当前场景的提示词规则。局部规则只适合表达已经确认的系统边界；如果问题来自职责断层、状态机缺失、helper 粒度不对或信息没有结构化传递，应优先修 helper / state / pipeline。

优先问：这个错误是模型忘记了一条规则，还是 workflow 没有把正确下一步做成确定性动作？如果是后者，继续加 prompt 只会让规则膨胀，应该把机制补上。

## Skill / helper / hook 分工

- Skill 负责 stage 语义、入口判断、交互节奏、人工协作和下一步说明。
- Arbor helper 负责确定性的状态读写、校验、上下文生成、安全搬运和窄命令执行。
- Hook 只守窄而硬的底线，不承担 package 拆分、contract 合理性、实现质量、review 结论等语义判断。

需要增强稳定性时，优先把不确定步骤转为确定性 helper 或测试，而不是增加口头禁令。

## 状态边界要明确

会影响安全、状态一致性或 workflow 边界的事实不能靠模型猜：

- 是否自动推进下一阶段。
- package 的交付边界。
- contract/dependency 边界。
- 哪些 helper 会修改 durable `.arbor` state。
- 哪个 artifact 是 source of truth，哪个只是导航层。

## Agent Team 与 subagent 使用边界

Claude Code 的 Agent Team 用于需要多 agent 协同的任务：teammates 是独立 Claude Code session，可以共享 task list、claim/complete tasks，并通过消息机制直接沟通、互相挑战和协调。适合并行 research/review、竞争性假设排查、跨模块协作等需要持续沟通的场景。

subagent 通过 `Agent` tool 在单个会话内派生，拥有独立 context window，适合自包含、无需与其他 worker 沟通、只需要把结果或摘要回传给主会话的任务。可用于隔离高噪音搜索、测试输出、局部审查或独立研究；多个 subagent 可并行，但由主会话管理和汇总，不应假定 subagent 之间会直接协作。

选择原则：需要 worker 之间直接沟通、共享任务状态或相互挑战时，用 Agent Team；只需要委派执行并回传结果时，用 subagent / `Agent` tool。

## 不让 workflow 层级膨胀

保持 workflow 骨架轻。新增阶段、固定 agent、runtime 编排和长期规则前，先问：

- 这个复杂度是否真的提升可控性或吞吐？
- 是否能用更小的 helper / schema / validation 解决？
- 是否只是为一次失败添加长期负担？

如果答案不明确，优先选择更少的阶段、更窄的职责和更确定的状态检查。
