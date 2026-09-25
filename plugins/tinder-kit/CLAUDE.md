# tinder-kit

次世代工程 Coding Agent 框架，专注于赋能强模型自主性、原子技能解耦与标准化驱动适配。

## 核心原则

1. **技能是提示词不是代码（零私有 CLI 脚本）**：
   > “Skills are instructions, not code. If an agent can do something with its native tools (Read, Grep, Glob), do NOT wrap it in a custom script.”
   > （技能是提示词不是代码。如果 Agent 能用原生工具搞定，绝对不要包装成自定义脚本！）
   - 彻底废除私有 CLI 工具（如 `forge` CLI、`wiki.py` 等脚本），拥抱 Claude Code 原生文件读写与标准工业设施。

2. **机制在插件，标准在项目**：
   - 插件提供流程规范、原子工程素养、Driver 驱动协议与测试 evidence 机制；
   - 项目定义自己的架构、设计品味与测试规则（`CLAUDE.md` / `DESIGN.md` / `.claude/rules/`）。

3. **单点驱动协议（Driver Pattern，收拢至 `.forge/`）**：
   - 由项目初始化（`/setup`）沉淀 `.forge/issue-tracker.md`，统一使用本地 Markdown 驱动协议（`.forge/`），零外部网络与 token 依赖；
   - 技能层仅面向抽象业务语义（“读取工单”、“发布工单”、“认领”、“结案”），由驱动协议卡片单点定义实际执行动作。

4. **双层技能分治（User-invoked vs. Model-invoked）**：
   - **User-invoked**（`disable-model-invocation: true`）：面向开发者场景的端到端编排主航道（`/develop`, `/grill-with-docs`, `/implement`, `/to-spec`, `/to-tickets`, `/wayfinder`, `/fix`, `/setup`），模型不得擅自调用；
   - **Model-invoked**：模型在执行过程中，根据具体工程情境自主判断、按需取用的工程素养工具箱（如 `research` 自动后台调研、`tdd`, `codebase-design`, `prototype`, `diagnose`, `review`, `grilling`, `domain-modeling`）。
