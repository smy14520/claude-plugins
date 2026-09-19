---
name: prototype
description: "Build a throwaway prototype or spike to answer design, UI, or library questions. Use when evaluating UX feel, spike testing third-party APIs, or when debating options that need a runnable demo."
---

# Prototype — 抛弃型探索探针

当面对“跑起来才知道”的设计分叉、第三方库能力摸底或 UI 手感直觉争议时，构建一个自包含、用完即弃的最小粗糙原型，获取第一手实证结论（Verdict）。

## 核心纪律（Discipline）

1. **绝对零测试税（Zero Testing Tax）**：
   - 探针的目标是验证可行性与感知，**严禁写单元测试、类型体操或追求代码整洁**；
   - 允许以最粗暴、直接的方式跑通核心链路（如单文件 HTML/JS、临时脚本）。
2. **严格物理隔离（Isolated Workspace）**：
   - 原型必须落入 `.forge/prototypes/<slug>/`；
   - 严禁将脏代码直接写进生产源码目录。
3. **交付实证结论（Empirical Verdict）**：
   - 原型运行并获得结论后，**在对话中显式输出 Verdict 摘要**（例如：“验证证实方案 B 在处理超长列表时帧率稳定在 60fps，方案 A 存在明显卡顿”）；
   - **Completion criterion**：Verdict 达成并折入 `spec.md` 或交接文档。原型代码弃置，不合入生产 Git 交付历史。

## 反模式（Anti-Patterns）

- **Gold-plating Prototypes**：为抛弃型探针编写单元测试、配置 CI、过度重构。
- **Direct-to-Production Bleed**：直接将未经验证和重构的原型脏代码打包合入生产环境。
- **Talking Over Running**：遇到可以通过 30 秒原型验证的事实，依然在对话中进行旷日持久的口头推测与争论。
