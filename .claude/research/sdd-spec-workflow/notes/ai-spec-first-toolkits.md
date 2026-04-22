# AI Spec-first Toolkits

## 当前结论

这一类样本（spec-kit、OpenSpec、Spec Kitty、Conductor）共同特点是：**把需求、设计、任务、执行上下文从聊天中抽出来，变成 repo 内工件，供人和 agent 共享**。区别主要在于它们如何定义阶段边界，以及流程治理强弱。

当前最值得关注的分化有三种：

1. **线性分层型**：spec-kit
   - constitution → spec → plan → tasks → implement
   - 适合把“全局原则”和“单功能规范”分层处理
   - 中介层清晰，利于窄职责 handoff

2. **变更集 / artifact-graph 型**：OpenSpec
   - current specs 与 per-change specs 分离
   - proposal / delta specs / design / tasks 围绕 change 目录组织
   - 更适合 brownfield 和增量迭代，不强制僵硬顺序

3. **强执行治理型**：Spec Kitty
   - 除了 spec / plan / tasks，还把 review / accept / merge / work packages / lane 都结构化
   - 适合高并发、多 agent、强追踪场景
   - 但对当前项目可能偏重

4. **可移植上下文型**：Conductor
   - 更强调长期上下文（product / tech-stack）和 agent 可迁移性
   - 提醒我们：workflow 若要跨工具，工件必须 repo-native

5. **harness + 注入自动化型**：Trellis
   - 把 `.trellis/spec/`、`.trellis/tasks/`、`.trellis/workspace/` 作为单一控制面，再投影到 Claude Code、Cursor、Codex 等多个平台
   - 不只定义工件，还通过 hooks / commands / agents 把 session start、before-dev、check、finish-work、parallel 等阶段自动化
   - 强调“repo 内共享标准 + task 生命周期 + workspace 记忆 + worktree 并发”一起构成 workflow

## 来源

- `../raw/ext-github-spec-kit.md`
- `../raw/ext-openspec.md`
- `../raw/ext-spec-kitty.md`
- `../raw/ext-conductor-flow.md`
- `../raw/ext-mindfold-trellis/_manifest.md`

## 这对需求意味着什么

如果当前项目的目标是 research → spec → task → impl 的**窄职责阶段**，那最贴近的不是完整照搬某个框架，而是吸收这几类样本的组合优势：

- 从 **spec-kit** 借“阶段边界清晰、工件分层明确”
- 从 **OpenSpec** 借“brownfield 友好、change-centric、可回写归档”
- 从 **Spec Kitty** 借“必要时把执行单元和 review 流制度化”，但不一定全盘接受 lane/dashboard
- 从 **Conductor** 借“长期上下文工件与 agent 可移植性”的视角
- 从 **Trellis** 借“repo-native 工件如何通过 hooks / commands / 多平台投影变成真正可执行 workflow”的视角

Trellis 还提醒了一个此前较弱的维度：如果 workflow 只定义文档层而不定义注入/切换/并行的运行机制，它更像静态模板；而 Trellis 把这些工件接到了 session lifecycle 和 agent orchestration 上，因此更接近完整 harness。

## 仍未解决的问题

- 当前项目是否真的需要独立的 project-level context artifact（类似 constitution / product / tech-stack）？
- 当前项目中的 spec 应该更接近 `feature contract`，还是更接近 `change proposal + design + tasks bundle`？
- 是否需要 archive / merge-back 机制，还是只要保持 spec 与 task 文件即可？

## 相关笔记

- `rfc-kep-and-doc-gates.md`
- `adr-and-decision-layer.md`
- `workflow-design-principles.md`
