---
name: develop
description: "End-to-end software development flow: align on intent, spike prototypes, implement with project standards, review, and endorse. Use when building a new feature, implementing a task, or starting development from scratch."
disable-model-invocation: true
---

# Develop — 端到端工程交付主航道

从需求对齐、深接缝确定，到全新上下文子 Agent 编码实现，再到客观双轴审查与防回归背书，一键贯通的现代化工程主流程。

## 核心运行哲学

1. **瘦协调器（Thin Coordinator）**：主会话只负责推移阶段和与人类高价值对齐，编码实现与测试分析由独立子 Agent 承担，主会话上下文 < 15k tokens；
2. **任务级隔离（Task-Scoped in `.forge`）**：不绑定 Git 分支，每个任务在 `.forge/tasks/<slug>/` 持有独立的 `state.json` 与文档链；
3. **物理上下文防爆（Handoff Chaining）**：每个阶段结束必须调用 `handoff` 蒸馏高信噪比交接文档，下一阶段子 Agent 只读交接文档，中间高噪音上下文就地释放；
4. **机制在插件，标准在项目**：编排层仅提供流程骨架与工具箱；具体是否写单测、如何验证、遵循何种架构风格，完全由项目本地 `CLAUDE.md` 与 `.claude/rules/` 决定。

---

## 阶段执行操典

### Phase 0: 路由与初始化 (Init & Resume)
1. 解析用户参数：`/develop [slug] "需求描述"`；
   - 若未提供 `slug`，从需求中推导极简小写短名（如 `jwt-refresh`）；
2. 检查 `.forge/tasks/<slug>/state.json`：
   - 若已存在且处于进行中：读取 `phase`，询问用户是否从上次断点接续；
   - 若新任务：执行 `forge new <slug> --title "需求标题"`；
3. **Completion criterion**：任务目录就绪，`state.json` 与初始 `spec.md` 存在。

---

### Phase 1: 意图对齐与接缝锁定 (Phase: ALIGN)
1. 调起 `grilling` 技能驱动决策树访谈：
   - 凡能查代码库的事实自行查证；
   - 挖掘核心诉求与边界，遇架构/术语变化调 `wiki` 技能维护项目规则与百科；
2. **拍定深接缝与验证依据（Agreed Seams & Verification Criteria）**：
   - 定义核心接口/模块契约签名与可观测行为预期；
   - 确定明确的 `Out of Scope`（必须经用户确认）；
3. 使用 `Edit` 工具将成果更新至 `.forge/tasks/<slug>/spec.md`；
4. 调用 `handoff` 技能产出 `handoffs/01-align.md`；
5. **Completion criterion**：
   - `spec.md` 包含具体的 Seams 契约与已确认的 Out of Scope；
   - `handoffs/01-align.md` 落盘；
   - 根据是否有未知探索需求，更新 `state.json` 的 `phase` 为 `EXPLORE` 或 `IMPLEMENT`。

---

### Phase 2: 抛弃型原型探索 (Phase: EXPLORE - 条件触发)
1. 派发 `forge-prototype` 子 Agent：
   - 在 `.forge/prototypes/<slug>/` 快速构建极简粗糙原型，零测试税；
2. 获取经验结论（Verdict），由用户感知或自测得出；
3. 将结论写入 `spec.md` 的 `## Empirical Findings`；
4. 调用 `handoff` 技能产出 `handoffs/02-explore.md`；
5. **Completion criterion**：
   - 屏幕上显示实证 Verdict 摘要；
   - 更新 `state.json` 的 `phase` 为 `IMPLEMENT`。

---

### Phase 3: 核心实现与工程纪律 (Phase: IMPLEMENT)
1. **派发【独立全新上下文】的 `forge-impl` 子 Agent**：
   - 使用 `Agent` 工具（`subagent_type="tinder-kit:forge-impl"`, `run_in_background: false`）；
   - **严格控制输入**：只传入 task_slug、`spec.md` 路径及最新 `handoff.md` 路径（项目 `CLAUDE.md` 与 rules 已由环境原生加载），绝不传入阶段 1 的冗长问答历史；
2. 子 Agent 自主协同与裁决：
   - **查阅项目标准**：读取项目 `CLAUDE.md` 与 `.claude/rules/`，明确项目规定的技术规范、架构准则与测试纪律；
   - **按需调用工具箱**：
     - 若项目要求自动化测试或涉及核心算法/契约：自发调用 `tdd` 在 Seams 上编写行为测试，先红后绿；
     - 若涉及模块结构设计：自发调用 `codebase-design` 设计深模块（薄接口，厚实现，信息隐藏）；
     - 若为纯界面、脚手架或无测试框架项目：按项目规定的标准执行可执行自验（命令行输出/界面呈现）；
3. 子 Agent 完成后调用 `handoff` 技能，将核心改动事实蒸馏入 `handoffs/03-impl.md`；
4. 子 Agent 会话销毁，高噪音执行垃圾被物理释放；
5. **Completion criterion**：
   - `handoffs/03-impl.md` 包含改动文件清单与验证通过记录；
   - 更新 `state.json` 的 `phase` 为 `REVIEW`。

---

### Phase 4: 双轴审查与防回归背书 (Phase: REVIEW)
1. **派发【只读全新上下文】的 `forge-review` 子 Agent**：
   - 使用 `Agent` 工具（`subagent_type="tinder-kit:forge-review"`, `run_in_background: false`）；
   - 输入：`git diff`、`spec.md` 中的 Seams 契约及 `handoffs/03-impl.md`；
2. 子 Agent 执行双轴审查：
   - **Standards 轴**：对照项目 `.claude/rules/` 审查代码坏味道与规范遵循度；
   - **Spec 轴**：审查是否忠实兑现了 Seams 约定，是否存在偷懒弱化断言；
3. 防回归验证：
   - 若项目配置了自动化测试套件，执行全量测试确认 100% 零回归；
   - 若项目未配置测试套件，记录可执行自验证据；
4. 生成并写入 `.forge/tasks/<slug>/endorsement.md`；
5. **Completion criterion**：
   - `endorsement.md` 包含验证背书与审查评级；
   - 更新 `state.json` 的 `phase` 为 `COMPLETED`。

---

### Phase 5: 成果呈递与交还控制权 (Presentation)
主会话向人类开发者呈递高浓度汇总：
1. **交付说明**：新功能的核心设计与实现亮点；
2. **背书钢印**：
   - 核心 Seams 验证状态；
   - 防回归验证结果；
   - 审查结论与规范核对情况；
3. **提示人类审查 `git diff` 并执行最终 Commit**。
