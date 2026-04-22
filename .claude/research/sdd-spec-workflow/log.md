# Research Log

## 2026-04-22
- 初始化 research 工作区：sdd-spec-workflow。
- 当前 framing：为后续 workflow 设计收集 SDD/spec-first 相关的优秀开源项目与方法论样本。
- 初步决定并行考察三类来源：
  1. 直接以 spec/spec-driven 命名的开源工作流项目
  2. 传统工程中的 RFC / design doc / ADR 驱动流程
  3. AI coding / agentic development 中以 spec 作为控制面的新实践
- 完成第一轮样本收集，落盘 raw 证据层：
  - github/spec-kit
  - Fission-AI/OpenSpec
  - Priivacy-ai/spec-kitty
  - create-conductor-flow / Conductor
  - forrestchang/andrej-karpathy-skills
  - Rust RFC
  - Kubernetes KEP
  - ADR + async PR decision making
- 完成第一轮主题笔记：
  - AI spec-first 工具链
  - RFC / KEP / 文档门禁流程
  - ADR 与决策记录层
  - 对当前项目最有价值的 workflow 设计原则
- 当前理解更新：
  - 真正重要的不是直接复制某个框架，而是提炼“何时进入重流程、工件如何分层、brownfield 如何处理、decision 层是否独立”这些结构原则。
  - karpathy-skills 补充了“全局行为规则层”的视角：单文件原则适合约束 agent 默认行为，但不能替代结构化 spec/task/handoff。
  - 当前研究已足够支持进入下一轮收敛，但还不适合直接冻结最终 workflow spec。
- 补充接入 `mindfold-ai/Trellis` 到 `sdd-spec-workflow` 工作区。
  - 该样本的价值不只是 spec/task 模板，而是把 `.trellis/spec/`、`.trellis/tasks/`、`.trellis/workspace/` 组合成一个可跨平台、可多 agent 复用的 AI harness。
  - 相比已有样本，Trellis 更强调 hook 驱动的 context injection、task lifecycle、parallel worktree execution，以及 repo 内共享标准在多工具间的投影。
  - 这让当前研究多出一个重要比较维度：workflow 的价值是否来自“工件结构本身”，还是来自“工件 + 平台集成 + 自动注入”的组合。
