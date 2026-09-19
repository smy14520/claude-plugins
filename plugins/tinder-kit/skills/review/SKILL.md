---
name: review
description: "Two-axis code review across Standards and Spec. Use when reviewing diffs, auditing changes before commit, verifying seam compliance, or when asked to 'review', 'code review', 'check diff'."
---

# Code Review — 双轴审查与防回归验证

以只读客观第三方视角审查工作树中的改动，隔离为互不污染的两个轴向：**代码规范与坏味道（Standards）** 与 **深接缝契约兑现度（Spec）**。

## 双轴审查程序

### 1. 确定审查范围与基准线
- 提取审查范围：`git diff`；
- 载入基准：`.forge/tasks/<slug>/spec.md`（重点看 `## Agreed Seams`）及项目根目录 `CONTEXT.md`。

### 2. 轴 1 审查：Standards 轴（代码与架构规范）
- 检查 Fowler 12 味代码坏味道（重复逻辑、发散变化、霰弹式修改、基本类型偏执等）；
- 检查深模块原则：公共接口是否足够薄？是否泄漏了底层存储或锁机制？
- 检查代码卫生：异常捕获是否精准、是否存在未释放的资源或潜在死锁；
- **小格式异味**：琐碎的格式或微小命名瑕疵直接给出修正示例，不长篇辩论。

### 3. 轴 2 审查：Spec 契约轴（深接缝吻合度）
- 逐一核验 `spec.md` 中的每个 Seam 是否在源码中有明确对应的入口；
- 检查测试真实性：**行为测试必须真实断言了 Seam 的输出与副作用**，严禁仅检查中间代理变量或注释断言。

### 4. 防回归与功能验证（Verification & Regression）
- 执行 Seam 验证命令（测试用例或自验命令），确保行为符合契约预期；
- 若项目配置了自动化测试套件，执行全量既有测试确保零回归；若无测试套件，根据项目规则记录可执行自验证据。

### 5. 审查结论呈递（Completion Criterion）
- **Completion criterion**：在对话中显式输出结构化背书报告：
  - **Standards 轴评级**：`CLEAN` 或列出带 `file:line` 的具体异味；
  - **Spec 轴评级**：`VERIFIED`（每个 Seam 均有坚实验证证据支撑）；
  - **防回归证明**：测试套件通过记录或自验执行输出。

## 反模式（Anti-Patterns）

- **Vague Approvals**：不给代码引用就下“整体看起来不错”等空洞结论。
- **Spec-Blind Reviewing**：不读 `spec.md` 直接根据代码盲猜意图，容易把原本的需求设计当 Bug 报。
- **Bikeshedding Over Critical Bugs**：在无伤大雅的命名和括号风格上耗费大量篇幅，忽略了核心契约的边界盲区。
