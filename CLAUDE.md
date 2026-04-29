# CLAUDE.md

本项目是 Claude Code plugin/workflow 实验仓库。协作时默认使用中文，优先保持流程清晰、状态确定、规则少而有力。

## 总原则

- **少即是多**：少做不必要的枚举、禁令和解释；给出清晰方向，并给模型留下合理判断空间。
- **提示词设计技巧沉淀到 rules**：可复用的 prompt/skill 写法、留白技巧和表达原则放在 `.claude/rules/prompt-design.md`，不要绑定到某一个具体原则或 skill。
- **skill 负责流程，arbor helper 负责机械动作，hook 只守底线**。
- 不要把可由代码、测试或 git 当前状态确认的信息写成长期记忆或重复文档；需要时直接读当前文件。
- 面向用户的 workflow 输出默认使用中文；代码、命令、schema 字段名保持项目既有风格。

## sdd-kit / Arbor 职责边界

- Skill 负责 stage 语义、流程入口、人工/agent 协作节奏和下一步说明。
- `arbor.py` / `arbor_core` 负责确定性的状态读写、校验、上下文生成、安全搬运和窄命令执行。
- 不要让 `arbor.py` 承担产品语义判断、实现质量判断或复杂 lead 决策；这些应留给 skill、review、人或 agent reasoning。
- 新增 helper 时优先做成小而确定的命令：给定输入，产生可预测的 `.arbor` 状态变更或文件搬运结果。
- 如果 lead/worker 需要记住一串易漏的 `cp`、`diff`、`patch`、状态更新步骤，优先考虑沉淀成 arbor helper，而不是增加长篇 prompt 规则。

## Workflow 设计偏好

- 保持 workflow 骨架轻：research/brainstorm/map/task/impl/review/parallel 各自职责要窄。
- Brainstorm/map 负责澄清上下文、架构取舍和 package 边界；task 只分解已经确定边界的可执行 package。
- 不要把 CLAUDE.md、rules 或已经自动加载的约束当成额外 discovery 工作重复阅读/总结，除非当前任务确实需要核对。
- 需要增强稳定性时，优先把不确定步骤转为确定性 helper 或测试，而不是增加口头禁令。
- `.wiki/` 是项目本地导航层，不是 source of truth；用它快速定位，再验证当前代码和 `.arbor`。

## Parallel / Agent Team 原则

- 默认保留 Agent Team 作为 parallel runtime，因为它提供 iTerm 可见窗口和可直接交互的 worker；不要默认替换成不透明 subagent。
- Main session 是 lead/orchestrator，负责协调、审查、checkpoint 和 runtime cleanup；不要直接实现 package/product diff，包括 serial integration 工作。
- `/parallel` 是动态吞吐优化：lane switch 只汇报，不等待确认；recoverable friction 先走 helper，只有真实 blocker 才停给用户。
- Worker 必须在自己的 worktree/branch 中工作；进入 worktree、验证 cwd/git root/branch、报告 `WORKTREE_READY` 后，才能读写或执行实现动作。
- Package worker 只修改声明的 `modification_scope`；跨 package 缺口通过 contract request 表达，不 patch sibling internals。
- Downstream implementation 只能依赖 mainline-visible facts：completed/merged/lead-integration/contract-update checkpoint；`reviewed` alone 不等于可依赖主干事实。
- Shared/global wiring、DI、routes、migration ordering、E2E assembly、repo-wide config 等属于 serial integration lane，不由普通 package worker 或 main-session lead 直接改。
- Team runtime 是临时运行态；完成或无可调度工作后应 shutdown workers 并 `TeamDelete`。不要隐式删除 worktree/branch/checkpoint，除非用户明确授权。

## Hooks 使用原则

- Hook 只用于窄而硬的 guardrail，例如阻止危险命令、提醒直接修改 `.arbor` control state、Stop 前提示未清理 runtime 或生成物。
- 不要用 hook 承担 package 拆分、contract 合理性、实现质量、review 结论等语义判断。
- Hook 的确定性来自脚本本身；LLM/agent 型 hook 只能作为建议，不应作为强 policy gate。
- `PostToolUse` 不能阻止已经发生的副作用；需要阻止时应使用合适的前置 hook 或 helper 校验。

## 测试与变更习惯

- 修改 workflow/helper 后要补对应单测；优先测试确定性 `.arbor` 状态、CLI 输出和边界行为。
- UI/frontend 变更必须实际启动并用浏览器验证；非 UI helper/workflow 变更至少运行相关单测和 `git diff --check`。
- 不要提交或保留测试生成的 `__pycache__` 噪音；如果历史上已有 tracked pycache，被测试改脏后要恢复。
- 不要为了兼容假想未来需求添加重型抽象；当文件过大时，优先按职责拆模块，而不是新增 workflow 层级。
