---
name: codebase-design
description: "Shared vocabulary and principles for deep modules, thin interfaces, and clean seams. Use when designing module interfaces, placing test seams, refactoring architecture, or making code AI-navigable."
---

# Codebase Design — 深模块设计哲学

提供源自 John Ousterhout《软件设计哲学》的核心设计标尺与统一词汇：**深模块、薄接口、干净接缝、信息隐藏**。它是架构演进与 TDD 确定测试接缝的统一准绳。

## 核心词汇与标尺（Vocabulary & Metrics）

1. **深模块（Deep Module） vs. 浅模块（Shallow Module）**：
   - **深模块**：极小的接口表面积，内部封装极其厚重的行为（如 Unix 文件 I/O 仅凭 `open/read/write/close` 四个方法隐藏了磁盘调度、缓存与文件系统的庞大复杂度）；
   - **浅模块**：接口的复杂度和它提供的行为几乎一样多（如仅包含 getter/setter 的贫血类、单行转发的空洞包装器），增加认知负荷却无实质抽象。
2. **测试接缝（Seam）**：
   - 模块对外最稳定、最核心的公共契约边界；
   - 外部调用者通过 Seam 观测行为，不可穿透接缝触碰内部细节；
   - **TDD 必须且只能在 Seams 上构建行为测试**。
3. **信息隐藏（Information Hiding）**：
   - 内部数据结构、锁、算法、缓存、第三方依赖库细节严禁泄露至公共接口；
   - 每个模块应当隐藏 1~2 个关键设计决策。
4. **零联动效应（Low Ripple Effect）**：
   - 修改一个深模块内部的算法或数据结构，调用方代码应当完全零改动。

## 反模式（Anti-Patterns）

- **Pass-through Methods / Middle Man**：没有任何实质逻辑、仅仅把参数转发给下一个函数的浅包装层。
- **Leaky Abstractions**：接口强迫调用方管理事务边界、底层重试次数或初始化顺序。
- **Barrel Files**：在目录根建立盲目 re-export 整个子树的大桶 index 文件，模糊了真正的模块边界，导致模块依赖分析失效。
- **Premature Generalization**：在出现两个真实独立的调用方之前，为了想象中的未来过早建立抽象层。
