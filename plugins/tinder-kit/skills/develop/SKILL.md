---
name: develop
description: "一键端到端工程交付主航道：对齐与深接缝锁定 → (可选原型探索) → 子 Agent TDD 实现 → 双轴审查与防回归背书 → 交付。基于 .forge 任务级隔离与 handoff 物理防爆。"
disable-model-invocation: true
---

# Develop — 端到端工程交付主航道

从需求对齐、深接缝确定，到全新上下文的子 Agent 编码实现，再到客观审查与防回归背书，一键贯通的现代化工程主流程。

## 核心运行哲学

1. **瘦协调器（Thin Coordinator）**：主会话只负责推移阶段和与人类高价值对齐，写代码和看大篇测试的脏活一律派发独立子 Agent，主会话总 Token < 15k；
2. **任务级隔离（Task-Scoped in `.forge`）**：不绑定 Git 分支，每个任务在 `.forge/tasks/<slug>/` 持有独立的 `state.json` 与文档链；
3. **物理上下文防爆（Handoff Chaining）**：每个阶段结束必须调用 `handoff` 蒸馏出百字信标，下一阶段子 Agent 只读信标，垃圾上下文就地销毁；
4. **深接缝背书（Seams Endorsement）**：废除死板 Gate，在商定的 2~3 个深接口上用 TDD 提供不可动摇的改动背书。

---

## 阶段执行流程

### 阶段 0: 路由与初始化 (Init & Resume)
1. 解析用户参数：`/develop [slug] "需求描述"`；
   - 若未提供 `slug`，从需求中推导极简小写短名（如 `jwt-refresh`）；
2. 检查 `.forge/tasks/<slug>/state.json`：
   - 若已存在且处于进行中：读取 `phase`，询问用户是否从上次断点接续；
   - 若新任务：执行 `forge new <slug> --title "需求标题"`。

---

### 阶段 1: 意图对齐与接缝锁定 (Phase: ALIGN)
1. 调起 `grilling` 技能驱动决策树访谈：
   - 绝不查户口，凡能查代码库的事实自行查证；
   - 挖掘核心诉求与边界，遇新业务概念调 `domain-modeling` 同步更新根目录 `CONTEXT.md`；
2. **双方拍定 2~3 个核心深接缝（Agreed Seams）**：
   - 定义接缝函数/接口签名与可观测行为预期；
   - 确定明确的 `Out of Scope`（必须经用户确认）；
3. 将成果更新至 `.forge/tasks/<slug>/spec.md`；
4. 调用 `handoff` 技能产出 `handoffs/01-align.md`；
5. 判断是否需要探索：
   - 若涉及未知技术选型或交互手感分叉：更新 `state.json` 的 `phase` 为 `EXPLORE`，进阶段 2；
   - 若技术方案清晰明确：更新 `state.json` 的 `phase` 为 `IMPLEMENT`，直接跳进阶段 3。

---

### 阶段 2: 抛弃型原型探索 (Phase: EXPLORE - 条件触发)
1. 派发 `forge-prototype` 子 Agent：
   - 在 `.forge/prototypes/<slug>/` 快速构建极简粗糙原型，零测试税；
2. 获取经验结论（Verdict），由用户感知或自测得出；
3. 将结论写入 `spec.md` 的 `## Empirical Findings`；
4. 调用 `handoff` 技能产出 `handoffs/02-explore.md`，更新 `phase` 为 `IMPLEMENT`，进入阶段 3。

---

### 阶段 3: 深模块实现与 TDD (Phase: IMPLEMENT)
1. **派发【独立全新上下文】的 `forge-impl` 子 Agent**：
   - 使用 `Agent` 工具（`subagent_type="tinder-kit:forge-impl"`, `run_in_background: false`）；
   - **严格控制输入**：只传入 task_slug、`spec.md` 路径、最新 `handoff.md` 路径及 `CONTEXT.md` 路径，绝不传入阶段 1 的冗长问答历史！
2. 子 Agent 内部自发协同：
   - 运用 `codebase-design` 设计深模块（薄接口，厚实现，信息隐藏）；
   - 运用 `tdd` 在商定的 Seams 上先写行为测试，确认变红后放手实现与重构；
   - 确保 Seams 测试全绿；
3. 子 Agent 完成后调用 `handoff` 技能，将核心改动事实蒸馏入 `handoffs/03-impl.md`；
4. 子 Agent 会话销毁，高噪音执行垃圾被物理释放；
5. 更新 `state.json` 的 `phase` 为 `REVIEW`，进入阶段 4。

---

### 阶段 4: 双轴审查与防回归背书 (Phase: REVIEW)
1. **派发【只读全新上下文】的 `forge-review` 子 Agent**：
   - 使用 `Agent` 工具（`subagent_type="tinder-kit:forge-review"`, `run_in_background: false`）；
   - 输入：`git diff`、`spec.md` 中的 Seams 契约及 `handoffs/03-impl.md`；
2. 子 Agent 执行双轴审查：
   - **Standards 轴**：审查代码坏味道、规范遵循度；
   - **Spec 轴**：审查是否忠实兑现了 Seams 约定，是否存在偷懒弱化断言；
3. 运行代码库全量既有测试，确认 100% 零回归；
4. 生成并写入 `.forge/tasks/<slug>/endorsement.md`；
5. 更新 `state.json` 的 `phase` 为 `COMPLETED`。

---

### 阶段 5: 成果呈递与交还控制权 (Presentation)
主会话向人类开发者呈递高浓度汇总：
1. **交付说明**：新功能的核心设计与实现亮点；
2. **背书钢印**：
   - 核心 Seams 行为测试：全部 PASS；
   - 全库防回归测试：全部 PASS；
   - 审查结论：Clean；
3. **提示人类审查 `git diff` 并执行最终 Commit**。
