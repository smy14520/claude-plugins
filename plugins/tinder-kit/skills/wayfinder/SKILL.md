---
name: wayfinder
description: "Map out huge, foggy efforts too big for one session as a shared decision graph. Resolves decisions one by one until the path is clear. Use for greenfield projects or massive architectural overhauls."
disable-model-invocation: true
---

# Wayfinder — 迷雾工程决策探路

适用于大而模糊的复杂系统重构或全新技术探索。当决策彼此交织、无法在一个会话内收敛时，构建决策地图，一张一张攻克决策票，直到迷雾散尽。

## 核心设计法则

1. **只产 Decisions，不产 Deliverables**：
   - 探路阶段专注消解架构未知，严禁在该阶段编写业务交付代码；
   - 解决一张票的唯一合格产物是一个拍定的硬决策与其依据（Resolution）。
2. **纯 Markdown 状态落盘在 `.forge/maps/<slug>/`**：
   - `map.md`：全局决策依赖网络（记录 open、closed 与当前可攻克的 frontier 节点）；
   - `tickets/T-NNN-<title>.md`：每张独立的决策票，声明其 `blocked_by` 依赖与待决问题。
3. **图清即交棒（Hand off when clear）**：
   - **Completion criterion**：地图上所有的 Frontier 决策票均已 Closed，迷雾区彻底清空；
   - 汇总核心决策集，生成综合交接文档，无缝移交至 `/develop` 正式立项开发。

## 反模式（Anti-Patterns）

- **Premature Implementation**：在决策图未清之前，顺手在探路会话中写了一大堆业务代码。
- **Unlinked Tickets**：创建了一堆扁平清单，没有显式声明票与票之间的 `blocked_by` 依赖关系。
- **Re-litigating Settled Tickets**：对已经 Closed 的决策票无端重新推翻讨论。
