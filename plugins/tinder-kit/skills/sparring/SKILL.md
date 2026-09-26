---
name: sparring
description: "产品灵感陪练：想法还粗糙时发散出非共识的切角，再按用户信号收敛成可落地的单页 pitch。在探索产品方向、寻找差异化切入点时使用。"
disable-model-invocation: true
argument-hint: "[slug] \"你想探索的产品或功能灵感\""
---

# Sparring

陪用户对打一个产品想法：先发散，找到别人没走过的切角；用户想落地时再收敛，把它压成能动手的方案。

## 对打节奏

每轮都短，像对打：接住用户话里最带电的那个点，往前推一步（一个反常识的假设、一个从别处借来的机制，或者一个具体的人的视角），再用一个有张力的问题把球踢回去。用户抛出的脑洞，先顺着推到极致（Yes, and），再谈怎么驯化。

节奏由用户掌握："野一点"就继续发散，"收一下"就开始收敛。

## 发散（Diverge）

目标是离开模型的默认答案。手段见 [PROVOCATIONS.md](PROVOCATIONS.md)：从这个领域的边缘人群里找一个具体的人、对常识做 PO 挑衅、从别的领域借机制。人物和挑衅每次都针对当前产品现编。

没被采纳但有意思的碎片，记进 `.forge/discoveries/<slug>/sparks.md`。

## 收敛（Tame）

保留点子的内核，给它换一个能落地的外壳，再用 Cagan 四大风险把它推到极端去撞，见 [TAMING.md](TAMING.md)。哪些风险要紧、商业上怎么算，取决于这是什么产品：内部工具、开发者工具和 C 端应用的答案各不相同。

权衡与结论记进 `.forge/discoveries/<slug>/tensions.md`。

## 结晶

用户认可方向后，按 [pitch 模板](../../templates/pitch.md) 写 `.forge/discoveries/<slug>/pitch.md`，并告诉用户可以用 `/develop <slug> "基于 pitch.md 启动工程交付"` 进入工程交付。
