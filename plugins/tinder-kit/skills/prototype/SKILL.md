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

选错分支会浪费整个原型。如果问题模糊且用户不在场，默认选择更贴近周围代码形态的分支（后端模块选 Logic，页面/组件选 UI），并在原型顶部醒目说明假设。

---

## 两个分支共用的规则（The Rules）

1. **Throwaway from Day One**：
   Logic 原型落在 `.forge/prototypes/<slug>/`；UI 原型放在目标页面旁边，名字带 `prototype`。
2. **Frictionless to Run**：
   启动必须极其无脑。Logic 原型是双击即开的单文件 HTML，UI 原型通过项目现成的一条命令启动。
3. **No Persistence by Default**：
   状态保存在内存中。持久化往往是被检验的对象。
4. **Zero Polish**：
   只写到能跑通、能回答问题为止。原型目标是以最小代价带回第一手实证结论，不做多余抽象。
5. **Surface the State**：
   在每次按钮动作或变体切换后，将当前相关的内部完整状态清晰渲染或打印出来，直观展示数据变化。
6. **Capture the Verdict**：
   验证完成后，在对话和交接文档中显式输出实证结论（Verdict）（例如：“验证证实状态机方案 B 在处理并发取消时状态不卡死”）。将验证过的决策折入生产代码或 `spec.md`，原型代码弃置。
