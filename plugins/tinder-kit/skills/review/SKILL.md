---
name: review
description: "客观独立上下文的双轴代码审查（Standards 代码规范与 Spec 契约兑现度）。在提交前核查 git diff、审计 Code smells、验证 Seams 契约与防回归测试时调用。"
---

# Code Review — 双轴代码审查

以只读客观第三方视角审查工作树中的改动，划分为两个独立的轴向：
- **Standards 轴**：代码是否遵循本项目既定的工程规范与质量基线？（“是否造得合规？”）
- **Spec 轴**：改动是否忠实兑现了初始需求与商定契约？（“造的是不是对的东西？”）

按轴分别独立输出结论，不用 Standards 的合规替代 Spec 契约的核验。

## 审查程序

### 1. 确定审查范围与输入基准
- 审查范围：`git diff` 及改动 commit 列表；
- 规格基准：`.forge/tasks/<slug>/spec.md`（重点关注 `## Agreed Seams` 与 `## Out of Scope`）；
- 规范基准：项目根目录 `CLAUDE.md` 及 `.claude/rules/`。

### 2. 轴 1 审查：Standards 轴（代码与工程规范）
1. **项目标准优先**：核对 diff 是否符合项目本地 `CLAUDE.md` 与 `.claude/rules/` 中声明的规则；
2. **Fowler Code smells 基线（启发式参考，项目标准高于基线）**：
   - **Duplicated Code**：相同或高度相似的逻辑形态在改动中重复出现；
   - **Feature Envy**：某个函数过度访问另一个模块/对象的数据，胜过访问自身；
   - **Primitive Obsession**：用基础字符串/字典代替了理应抽离的独立实体；
   - **Shotgun Surgery**：单项逻辑变更导致改动散落在过多不相关的文件中；
   - **Divergent Change**：同一个模块因多种不相干的原因被同时修改；
   - **Speculative Generality**：增加了当前契约并未要求的抽象层、多余参数或钩子；
   - **Middle Man**：存在仅仅将调用转发给下一层的空洞包装层；
3. **判定原则**：分清硬性违规（违反项目 rules）与权衡建议（Code smells 启发）。

### 3. 轴 2 审查：Spec 轴（需求与 Seams 契约兑现度）
对照 `spec.md` 逐条核查改动代码与测试，指出 `spec.md` 对应行：
1. **功能遗漏或残缺**：spec 要求了但源码中缺失或未完整实现的条目；
2. **私自扩充（Scope Creep）**：spec 未要求或明确列在 `Out of Scope` 中，却被私自写进代码的行为；
3. **契约实现错误**：声称已实现，但输入输出、边界容错或副作用不符合商定 Seam 的条目；
4. **测试有效性**：验证测试是否真实断言了 Seam 的公开行为与副作用，而非恒真的 Tautological test（自我印证假测试）。

### 4. 验证与防回归（Verification）
- 运行针对商定 Seams 的验证命令，确认全部真实通过；
- 若项目配置了自动化测试套件，执行全量既有测试确保零回归；若无自动化套件，按项目规则记录自验证据。

### 5. 审查结论呈递（Completion Criterion）
在对话中输出结构化审查报告：
- `## Standards 轴结论`：评级（CLEAN / ISSUES），发现的规范违规与 Code smells 清单（注明 `file:line` 与修改建议）；
- `## Spec 轴结论`：评级（CLEAN / ISSUES），Seams 契约兑现核验结果（注明 `spec.md` 对应行号，标注通过/残缺/越界）；
- `## 防回归验证`：测试命令与 exit code 记录；
- `## 交付就绪确认`：双轴均通过时提示准备就绪，由人类执行 Commit。
