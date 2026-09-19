# tinder-kit

次世代工程 Coding Agent 框架，专注于赋能强模型自主性、原子技能分治解耦、与长程上下文安全。

## 核心原则

1. **机制在插件，标准在项目**：
   - 插件提供流程编排、原子工程素养、交接防爆与背书网络；
   - 项目定义自己的架构、设计品味与测试规则（`CLAUDE.md` / `DESIGN.md` / `.claude/rules/`）。

2. **专属目录：`.forge`（任务级自包含隔离）**：
   - 绝不做全局单例状态，不强行绑定 Git 分支；
   - 每一个需求/缺陷独立自包含在 `.forge/tasks/<task-slug>/`；
   - 目录内持有专属的 `state.json`（轻量飞行仪表）、`spec.md`（需求与深接缝 Seams）以及 `handoffs/`（阶段交接文档链）。

3. **双层技能分治（User-invoked vs. Model-invoked）**：
   - **User-invoked**（`disable-model-invocation: true`）：面向开发者场景的端到端编排主航道（如 `/develop`）与高阶意图对齐入口，模型不得擅自调用；
   - **Model-invoked**：模型在执行过程中，根据具体工程情境自主判断、按需取用的工程素养工具箱（如 `tdd`, `codebase-design`, `prototype`, `diagnose`）。

4. **深接口（Seams）与测试背书（Endorsement），而非死板 Gate**：
   - 废除单 slice 机械拦截与熔断惩罚，把重构自由还给模型；
   - 在系统深接缝（Seams）上编写高杠杆端到端行为测试与核心单元测试，作为交付时的不可动摇背书。

5. **Handoff 上下文物理防爆**：
   - 编排流中每个阶段完成时，必须将高噪音的执行细节蒸馏为一份标准 `handoff.md`；
   - 下一阶段由独立上下文的子 Agent 接棒，只读交接文档，彻底斩断长程会话的上下文膨胀与衰减。
