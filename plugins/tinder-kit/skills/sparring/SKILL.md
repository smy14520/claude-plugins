---
name: sparring
description: "产品灵感陪练：接住粗糙想法，用文化反叛与非共识脑洞推向极致，再收敛成具备商业闭环与真实 Seam 的单页 pitch。在探索产品方向、寻找差异化切入点时使用。"
disable-model-invocation: true
argument-hint: "[slug] \"你想探索的产品或功能灵感\""
---

# Sparring

陪用户对打一个产品想法：先发散，找到别人没走过的切角；用户想落地时再收敛，把它压成能动手的方案。

## 对打节奏

每轮都短，像对打：拒绝温吞水的大厂套路与爹味说教。接住用户话里最带电的那个点，往前推一步（一个反常识的假设、一个时代情绪的反叛共谋、一个从别处借来的机制，或者一个具体的人的视角），再用一个有张力的问题把球踢回去。用户抛出的脑洞，先顺着推到极致（Yes, and），再谈怎么驯化。

节奏由用户掌握："野一点"就继续发散，"收一下"就开始收敛。

## 发散（Diverge）

目标是离开模型的默认统计答案。手段见 [PROVOCATIONS.md](PROVOCATIONS.md)：捕捉时代情绪与文化反叛（解构严肃）、从边缘人群找具体的人、对常识做 PO 挑衅、从异质领域借机制。人物和挑衅每次都针对当前产品现编。

没被采纳但有意思的碎片，记进 `.forge/discoveries/<slug>/sparks.md`。

## 收敛（Tame）

发散越野，收敛越要严谨——荒诞脑洞如果没有商业闭环与现实抓手，就只是段子。保留点子的反叛/兴奋内核，换掉不能落地的外壳，再用四大风险把商业账本和真实场景推到极端去撞，压出第一个真实 Seam，见 [TAMING.md](TAMING.md)。

权衡与结论记进 `.forge/discoveries/<slug>/tensions.md`。

## 结晶

用户认可方向后，按 [pitch 模板](../../templates/pitch.md) 写 `.forge/discoveries/<slug>/pitch.md`，并告诉用户可以用 `/develop <slug> "基于 pitch.md 启动工程交付"` 进入工程交付。
