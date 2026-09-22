---
name: prototype
description: "构建一次性 Spike / Throwaway 原型来回答关键设计问题。适用于验证状态模型手感是否顺畅、或探索界面应该长什么样时调用。"
---

# Prototype — Spike 原型探索

原型（Prototype）是**专门用来回答一个具体疑问的一次性 Spike 代码（Throwaway Code）**。问题的形态决定原型的结构。

---

## 分支决断（Pick a Branch）

动手前，首先识别你到底在回答哪个层面的问题：

- **"这个业务逻辑 / 状态模型跑起来手感对不对？"** ➔ 见 [LOGIC.md](LOGIC.md)
  构建一个**单一、自包含、可分享的 HTML 文件**。包含状态数据面板、自由操作按钮，以及分 Tab 的引导式真实业务场景走查（Guided Walkthroughs），让非技术人员双击即可打开并感受底层状态机。
- **"这个界面 / 交互布局应该长什么样？"** ➔ 见 [UI.md](UI.md)
  生成 **3 种截然不同（Radically Different）的 UI 变体**，支持通过浮动底栏或 URL 参数一键切换对比，辅助人类迅速拍定视觉与排版方案。

选错分支会彻底浪费整个原型。如果问题模糊且用户不在场，默认选择更贴近周围代码形态的分支（后端模块选 Logic，页面/组件选 UI），并在原型顶部醒目说明假设。

---

## 适用于两个分支的六大通用铁律（The 6 Rules）

1. **从第一天就是抛弃型（Throwaway from Day One）**：
   原型严格落盘在 `.forge/prototypes/<slug>/`（受项目 `.gitignore` 保护），或明确带有 `prototype` 命名前缀。严禁将未经验证的 Spike 原型脏代码直接混入生产业务目录。
2. **运行零心智负担（Frictionless to Run）**：
   启动必须极其无脑。Logic 原型必须是双击即开的单文件 HTML，UI 原型通过项目现成的一条命令启动。
3. **默认不持久化（No Persistence by Default）**：
   状态一律保存在内存中。持久化往往是被检验的对象，绝不该成为原型的运行依赖。
4. **绝对零测试税与跳过修饰（Zero Polish & Zero Testing Tax）**：
   **严禁写单元测试**，严禁做超过“能跑通验证”之外的多余错误处理与过度抽象。原型的唯一目标是以最小代价带回第一手实证结论。
5. **状态必须显影（Surface the State）**：
   在每次按钮动作或变体切换后，必须将当前相关的内部完整状态清晰渲染或打印出来，让人类直观看到数据发生了什么变化。
6. **完工沉淀实证结论（Capture the Verdict）**：
   验证完成后，**在对话和交接文档中显式输出实证结论（Verdict）**（例如：“验证证实状态机方案 B 在处理并发取消时状态不卡死”）。将验证过的决策折入生产代码或 `spec.md`，原型代码弃置。

---

## 反模式（Anti-Patterns）

- **Gold-plating Prototypes**：为一次性探针编写完整的单元测试、CI 配置或过度架构重构。
- **Direct-to-Production Bleed**：直接将未经验证和重构的原型代码原样打包并合入生产主分支。
- **Talking Over Running**：明明跑个粗糙探针 2 分钟就能验证的事实，却在对话中长篇大论争论方案 A 好还是方案 B 好。
