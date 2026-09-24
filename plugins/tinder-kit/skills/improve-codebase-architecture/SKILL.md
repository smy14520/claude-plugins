---
name: improve-codebase-architecture
description: "全代码库架构体检与深化重构大扫除：扫描浅模块、重复影子工具类与散碎逻辑，评估 Deletion test，在临时目录输出可视化 HTML 报告，并围绕选定候选项展开 grilling 决策树访谈。仅由人类显式调用。"
disable-model-invocation: true
---

# Improve Codebase Architecture — 全代码库架构体检与大扫除

面向存量代码库的**定期架构巡检与结构深化**工具（建议每隔数天或在开启重大特性前运行一次）。
以 `codebase-design` 的**深模块哲学（Deep Modules）**为标尺，清除全仓库中到处散落的浅包装层（Shallow Pass-throughs）、重复发明轮子的影子工具函数（Shadow Utils）与高耦合碎片，提升整个系统的**可测性（Testability）**与 **AI 可导航性（AI-navigability）**。

恪守原则：**“本技能只做勘测与诊断，绝不直接就地修改业务代码”**。产物是一份独立的临时 HTML 报告与针对选定候选的决策树访谈。

---

## 核心执行流程

### 1. 勘测与确定扫描重心（Explore & YAGNI Scope）
1. **范围聚焦（YAGNI Scoping Filter）**：
   - 若用户指定了特定目录/子系统/痛点（如 `/improve-codebase-architecture "auth"`），紧扣指定范围；
   - 若未指定，**读取近期提交记录（`git log --oneline -20`）**：将勘测重心偏向近期高频改动的活跃代码路径。
     （*哲学依据：在没人修改的冷门代码处做架构深化是无意义的过度折腾；在正在演进的代码热区深化才能即刻收回重构杠杆*）；
2. **知识对齐**：
   - 调阅存量 Wiki（`.forge/wiki/concept/` 与 `.forge/wiki/decision/`），使用业务领域统一词汇，不翻案既定 ADR 架构决策；
3. **寻找架构摩擦与浅模块（Hunt for Shallowness）**：
   派一个子 Agent 遍历活跃代码（保持主会话干净），以 `codebase-design` 的词汇与标尺记录摩擦点：
   - **影子工具函数与轮子泛滥**：哪里在多个地方手写了高度相似的基础解析、日期格式化、字符串拼装？
   - **散碎跳跃**：理解一个业务概念是否需要同时在 5 个细碎的小文件之间跳来跳去？
   - **测试驱动形而上学**：哪里只是为了单测硬把纯函数抽出来，而真实的 Bug 全藏在各个调用方的组合时序里（缺乏 **Locality**）？
   - **接口过宽（Shallow Module）**：哪些模块对外暴露的 interface 复杂度几乎等于内部实现？
4. **黄金过滤器：Deletion test（模块删除检验）**：
   对每一个疑似浅模块执行假设检验：
   *“如果把这个模块删掉，系统的复杂度是被收拢隐藏到了更小更厚的 interface 之后，还是被迫散落到了各个调用方？”*
   **只有答案是“复杂度被收拢集中（Concentrates complexity）”的重构点，才具备立项价值！**

---

### 2. 输出可视化自包含 HTML 报告（Self-Contained HTML Report）
1. **零污染落盘**：
   - 将 HTML 报告写入操作系统临时目录（从 `$TMPDIR` 读取，缺省回退 `/tmp`），文件名为 `architecture-review-<timestamp>.html`，**绝对不向代码库提交任何临时报告文件**；
2. **报告呈现标准**：
   - 引入 Tailwind（CDN）排版与 Mermaid（CDN）绘制架构图，排版直观大方；
   - 包含紧凑图例：实线框 = 模块，虚线 = Seam，红箭头 = 逻辑泄漏/耦合，粗黑框 = 深模块；
   - 罗列最具价值的深化候选项，每个卡片包含：
     - **Title**：精准动作命名（如“收拢散碎的日期解析与时区转换模块为 Deep Time 模块”）
     - **Badge**：推荐强度标签（`Strong` / `Worth exploring` / `Speculative`）
     - **Files**：涉及的源文件路径列表
     - **Problem**：痛点说明（一句话讲清为什么当前架构产生摩擦）
     - **Solution**：重构方案（一句话讲清合并与下沉形态）
     - **Benefits**：收益归因（以 **Locality 内聚** 与 **Leverage 杠杆** 解释，指出哪些测试得以大幅简化）
     - **Before / After 架构对比图**：清晰展示重构前后模块深度与 Seam 边界变化；
3. **在浏览器自动打开**：
   - 在终端输出报告绝对路径，并尝试在宿主浏览器打开展示（macOS 使用 `open <path>`，Linux 使用 `xdg-open <path>`）。

---

### 3. 决策树访谈与后续闭环（Grilling Loop & Next Steps）
1. 报告呈递后，AI 给出自身最建议优先实施的 **Top 推荐候选**，并询问用户：“你想先深入推进哪一个？”；
2. 用户选定某个候选后，**同时调用 `grilling` 与 `domain-modeling`** 展开决策树访谈（新的领域术语由 domain-modeling 当场记录）：
   - 敲定深化后模块的 interface 签名与公共行为；想并排比较几种截然不同的接口时，按 `codebase-design` 的 [DESIGN-IT-TWICE.md](../codebase-design/DESIGN-IT-TWICE.md) 并行派子 Agent 各设计一版；
   - 确定测试存留策略与防回归 Seam；
   - 若用户决定放弃某个候选，可记录一条轻量 ADR 防止后续巡检重复提议；
3. 访谈收敛后，提示用户：
   > “架构深化方案已敲定！接下来请运行 `/develop <slug>`（或 `/to-spec`）作为独立的工程任务稳健实施交付。”
