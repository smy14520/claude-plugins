---
name: wayfinder
description: "迷雾探路流：用于大而模糊的复杂系统设计，将交织的决策链拆解为决策图与决策票（只产 decisions 不产 deliverables），在 .forge/maps/ 维护，图清后再转 /develop。"
disable-model-invocation: true
---

# Wayfinder — 迷雾工程决策探路

当一个系统重构或新特性过于宏大、决策彼此咬合缠绕，无法在一个会话中收敛时，使用 Wayfinder 绘制决策地图，一张一张攻克决策票，直到迷雾消散、路径清晰。

## 核心设计法则

1. **只产 Decisions，不产 Deliverables**：
   - 探路阶段严禁写业务交付代码；
   - 解决一张票的产物是一个拍定的硬决策与依据（Resolution）；
2. **状态纯文本化落盘在 `.forge/maps/<slug>/`**：
   - `map.md`：全局决策网络地图（包含 open, closed 与 frontier 节点）；
   - `tickets/T-NNN-<title>.md`：每张独立的决策票，声明其 `blocked_by` 依赖；
3. **图清即交棒（Hand off when clear）**：
   - 当地图上所有的 Frontier 与雾区被全部拍定闭合（All Tickets Closed）；
   - 汇总决策集，无缝交棒给 `/develop` 正式立项开工！
