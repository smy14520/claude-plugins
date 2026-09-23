---
name: develop
description: "端到端工程交付主航道：需求意图对齐、Seams 契约锁定、独立子 Agent 隔离编码、客观双轴审查与防回归 evidence。在构建新功能、从零开发任务或进行重大功能迭代时使用。"
disable-model-invocation: true
---

# Develop — 端到端工程交付主航道

从需求对齐、Seams（可观测行为边界）锁定，到全新上下文子 Agent 编码实现，再到客观双轴审查与防回归 evidence，一键贯通的现代化工程主流程。

## 核心运行哲学

1. **瘦协调器（Thin Coordinator）**：主会话只负责推移阶段和与人类高价值对齐，编码实现与测试分析由独立子 Agent 承担，主会话上下文 < 15k tokens；
2. **任务级隔离（Task-Scoped in `.forge`）**：不绑定 Git 分支，每个任务在 `.forge/tasks/<slug>/` 持有独立的 `state.json` 与文档链；
3. **上下文隔离（Handoff Chaining）**：每个阶段结束将高信噪比交接文档写入 `handoffs/`，下一阶段子 Agent 只读交接文档，释放中间上下文；
4. **机制在插件，标准在项目**：编排层仅提供流程骨架与工具箱；具体是否写单测、如何验证、遵循何种架构风格，完全由项目本地 `CLAUDE.md` 与 `.claude/rules/` 决定。

---

## 阶段执行步骤

### Phase 0: 路由与初始化 (Init & Resume)
1. 解析用户参数：`/develop [slug] "需求描述"`；
   - 若未提供 `slug`，从需求中推导极简小写短名（如 `jwt-refresh`）；
2. 检查 `.forge/tasks/<slug>/state.json`：
   - 若已存在且处于进行中：读取 `phase`，询问用户是否从上次断点接续；
   - 若新任务：执行 `forge new <slug> --title "需求标题"`；
3. **Completion criterion**：任务目录就绪，`state.json` 与初始 `spec.md` 存在。

---

### Phase 1: 意图对齐与 Seams 锁定 (Phase: ALIGN)
1. **存量记忆检索（Grounding）**：
   - 使用 `Read` 工具查阅 `.forge/wiki/index.md`（若存在），检索涉及模块的历史决策（`decision/`）、跨文件拓扑（`cross_cut/`）与已知 Gotcha（`gotcha/`），作为已知底座；
2. **启动前沿访谈**：
   - 明确执行：**Call the Skill tool for "grilling"** 驱动决策树访谈；
   - 仅针对真正分歧与业务取舍提问（带编号、推荐项与理由），直至消除所有隐藏假设；
3. **拍定 Seams 与验收标准（Agreed Seams & Verification Criteria）**：
   - 确立本次改动对外公开的 **Seams（可观测行为边界 / Public Contract）**：
     - *什么是 Seam*：系统在不侵入内部细节的前提下，对外展现行为与可供验证的公共接触面（CLI 的入参与退出码、API 的请求与响应、前端用户的交互与视觉反馈）；
     - 拒绝内部函数耦合，只锁定外部契约与验证依据；
   - 明确 `Out of Scope`（经用户确认）；
4. 使用 `Edit` 工具将成果更新至 `.forge/tasks/<slug>/spec.md`；
5. 生成阶段交接文档至 `.forge/tasks/<slug>/handoffs/01-align.md`；
6. **Completion criterion**：
   - `spec.md` 包含具体的 Seams 契约与已确认的 Out of Scope；
   - 对应交接文档落盘；
   - 根据是否有未知探索需求，更新 `state.json` 的 `phase` 为 `EXPLORE` 或 `IMPLEMENT`。

---

### Phase 2: Spike 原型探索 (Phase: EXPLORE - 条件触发)
1. 派发 `forge-prototype` 子 Agent：
   - 在 `.forge/prototypes/<slug>/` 快速构建极简粗糙的 Throwaway Prototype，零测试税；
2. 获取经验结论（Verdict），由用户感知或自测得出；
3. 将结论写入 `spec.md` 的 `## Empirical Findings`；
4. 生成阶段交接文档至 `.forge/tasks/<slug>/handoffs/02-explore.md`；
5. **Completion criterion**：
   - 屏幕上显示实证 Verdict 摘要；
   - 更新 `state.json` 的 `phase` 为 `IMPLEMENT`。

---

### Phase 3: 核心实现与派发 (Phase: IMPLEMENT)
1. **派发【独立全新上下文】的 `forge-impl` 子 Agent**：
   - 使用 `Agent` 工具（`subagent_type="tinder-kit:forge-impl"`, `run_in_background: false`）；
   - **输入**：只传入 task_slug、`spec.md` 路径及最新 `handoff.md` 路径；
2. 等待子 Agent 执行完毕并回收交付成果；
3. 子 Agent 会话销毁，释放上下文；
4. **Completion criterion**：
   - 核心改动已落盘，生成了最新实现交接文档；
   - 更新 `state.json` 的 `phase` 为 `REVIEW`。

---

### Phase 4: 双轴审查与防回归 evidence (Phase: REVIEW)
1. **派发【只读全新上下文】的 `forge-review` 子 Agent**：
   - 使用 `Agent` 工具（`subagent_type="tinder-kit:forge-review"`, `run_in_background: false`）；
   - 输入：`git diff`、`spec.md` 中的 Seams 契约及最新实现交接文档；
2. 等待审查子 Agent 产出双轴审计结论与 evidence；
3. **Completion criterion**：
   - `endorsement.md` 包含验证 evidence 与审查评级；
   - 更新 `state.json` 的 `phase` 为 `COMPLETED`。

---

### Phase 5: 知识晋升、成果呈递与交还控制权 (Presentation & Promotion)

主会话收尾，向人类开发者呈递汇总：

1. **知识晋升与 Spec 归档（Promotion & Archiving）**：
   - **Spec 归档（Delta 归档）**：`.forge/tasks/<slug>/spec.md` 伴随任务完成立即冻结归档，封入任务历史；现状以代码和测试为准；归档的 spec 只当历史；
   - **知识晋升（State 沉淀）**：若本任务产生了不可逆架构决策、跨系统联动拓扑、新领域实体或 Gotcha，使用 `Write` 工具将决策沉淀至 `.forge/wiki/decision/` 或提议写入 `.claude/rules/`；
2. **Evidence 呈递**：
   - 核心 Seams 行为契约兑现情况；
   - 全量防回归测试结果（或 `perceive` 实际运行证据截图/日志）；
   - 双轴审查评级；
3. **交付说明与控制权交还**：
   - 呈现新功能的核心亮点与改动文件清单；
   - **提示人类审查 `git diff` 并执行最终 Commit**（提交权永远属于人类）。
