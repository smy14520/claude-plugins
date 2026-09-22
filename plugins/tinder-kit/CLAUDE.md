# tinder-kit

次世代工程 Coding Agent 框架，专注于赋能强模型自主性、原子技能分治解耦、与长程上下文安全。

## 核心原则

1. **机制在插件，标准在项目**：
   - 插件提供流程编排、原子工程素养、交接防爆与背书网络；
   - 项目定义自己的架构、设计品味与测试规则（`CLAUDE.md` / `DESIGN.md` / `.claude/rules/`）。

2. **专属目录：`.forge`（任务级自包含隔离）**：
   - 绝不做全局单例状态，不强行绑定 Git 分支；
   - 每一个需求/缺陷独立自包含在 `.forge/tasks/<task-slug>/`；
   - 目录内持有专属的 `state.json`（轻量飞行仪表）、`spec.md`（需求与可观测行为边界 Seams）以及 `handoffs/`（阶段交接文档链）。

3. **双层技能分治（User-invoked vs. Model-invoked）**：
   - **User-invoked**（`disable-model-invocation: true`）：面向开发者场景的端到端编排主航道（如 `/develop`）与高阶意图对齐入口，模型不得擅自调用；
   - **Model-invoked**：模型在执行过程中，根据具体工程情境自主判断、按需取用的工程素养工具箱（如 `tdd`, `codebase-design`, `prototype`, `diagnose`）。

4. **Seams 契约与测试背书（Endorsement），而非死板 Gate**：
   - 废除单 slice 机械拦截与熔断惩罚，把重构自由还给模型；
   - 在系统 Seams（可观测行为边界 / Public Contract）上编写高杠杆端到端行为测试与核心单元测试，作为交付时的不可动摇背书。

5. **Handoff 上下文物理防爆**：
   - 编排流中每个阶段完成时，必须将高噪音的执行细节蒸馏为一份标准 `handoff.md`；
   - 下一阶段由独立上下文的子 Agent 接棒，只读交接文档，彻底斩断长程会话的上下文膨胀与衰减。

6. **大小需求分流：主航道 vs. 免 Spec 快车道（Fast-Track）**：
   - **主航道（`/develop`）**：面向中大型功能、跨模块交互、架构演进。走 Seams 契约锁定、子 Agent 物理隔离编码与双轴审查背书；
   - **免 Spec 快车道（Fast-Track）**：面向日常参数微调、单点小改动。**坚决反对形式主义，免建 `.forge/tasks/`，免写 `spec.md`**。模型自主执行“敏捷反射三板斧”：
     1. 查 Wiki 决策与暗坑（避开历史踩过的雷）；
     2. Git 提交历史考古（`git log -L` / `git log -S` 查阅当时为什么这么写）；
     3. 就地改动，运行既有测试或 `perceive` 自验，30 秒极速交付。

7. **增量（Delta）与存量（State）分离（终结 PRD 坟场）**：
   - 任务的 `spec.md` 是临时施工单（Delta），完工交付立即冻结归档，未来任务绝不将其当作现状真相读取；
   - 代码与活的 Seam Tests（可执行契约测试）是系统现状（State）的唯一执行真相；
   - Wiki 只做“知识晋升”，仅收录不变量、ADR、领域概念与跨系统拓扑，绝不搬运流水账需求。
