---
name: codebase-design
description: "用于设计深模块（Deep Modules）的共享词汇与核心标尺。适用于设计或改进模块接口、寻找深化机会、决定 seam 放在哪里、提升系统可测性时调用。"
---

# Codebase Design

设计 **deep modules（深模块）**：把大量行为放在小 interface 之后，把 interface 放在清晰 seam 上，并通过该 interface 进行端到端行为测试。凡是在设计新功能或重构既有代码时，统一使用这套语言和原则。

目标是：**给 callers 带来 leverage（杠杆），给 maintainers 带来 locality（内聚与防扩散），并让每个人都更容易进行自动化测试。**

---

## 统一词汇表（Glossary）

准确使用这些术语，不要替换成 "component"、"service"、"API" 或 "boundary"。一致的语言就是力量。

- **Module（模块）**：任何拥有 interface 和 implementation 的实体。故意不限定尺度：函数、类、包或跨层切片皆可。（避免使用：unit, component, service）
- **Interface（接口）**：调用方为了正确使用该 module 必须知道的**一切事实**：不仅是类型签名（type signature），还包括不变量（invariants）、时序约束（ordering constraints）、错误模式（error modes）、必要配置与性能特征。（避免使用：API, signature，这些词太窄，仅指表面类型）
- **Implementation（实现）**：module 内部的代码体。它不同于 **Adapter**：一个东西可以是小 adapter 但有大 implementation（如真实的 Postgres repo），也可以是大 adapter 但 implementation 很小（如内存 fake）。讨论 seam 时说 adapter；其他时候说 implementation。
- **Depth（深度）**：interface 上的杠杆（leverage）：调用方（或测试）每理解一单位 interface，就能撬动多少实质行为。大量复杂行为藏在小接口之后时，module 是 **deep**；接口复杂度几乎和内部实现一样多时，module 是 **shallow**。
- **Seam（Michael Feathers）**：可以在不直接修改当前文件源码的情况下改变行为的地方；也就是 module 的 interface 所在的*物理位置*（可观测行为边界）。Seam 放在哪里是独立的设计决策，不同于 Seam 后面藏着什么。（避免使用：boundary，它与 DDD 的 bounded context 混淆）
- **Adapter（适配器）**：在 seam 上满足某个 interface 的具体实例。描述的是 *role（填哪个槽位）*，而不是 substance（内部是什么）。
- **Leverage（调用杠杆）**：调用方从 Depth 获得的收益：每学习掌握一单位 interface，就能获得极大能力。一次实现可在 N 个调用处和 M 个测试中持续收回认知成本。
- **Locality（维护内聚）**：维护者从 Depth 获得的收益：改动、Bug 排查、业务知识与测试验证集中在一处，而不是散落到各个调用方中。修一次，到处生效。

---

## Deep vs. Shallow（深模块 vs. 浅模块）

```text
Deep module（深模块，极力推崇）:
+------------------+
| Small Interface  | -> 方法极少、参数精炼、易懂
+------------------+
|                  |
| Deep             | -> 内部隐藏复杂的算法、状态机与排障防御
| Implementation   |
|                  |
+------------------+

Shallow module（浅模块，坚决避免）:
+-------------------------------+
| Large Interface               | -> 方法繁多、暴露过多参数与配置
+-------------------------------+
| Thin Implementation           | -> 内部大半只是空洞的参数转发（Pass-through）
+-------------------------------+
```

设计 interface 时时刻自问：
1. 我能减少对外暴露的方法数量吗？
2. 我能简化参数列表吗？
3. 我能把更多复杂的内部细节隐藏在 Seam 之后吗？

---

## 核心设计法则（Principles）

1. **Depth 是 interface 上的杠杆属性，不是代码行数。**
   深模块内部可以由许多小的、可替换的子部件组成，只要它们不泄露到 interface 上即可。模块可以拥有内部测试专用的 **internal seams**，以及对外暴露的 **external seam**。
2. **Deletion test（模块删除检验）**：
   想象把这个 module 彻底删掉：
   - 如果系统的复杂度瞬间消失了，说明它只是个多余的浅包装层（Pass-through）；
   - 如果它的复杂度被迫重新散落到全系统 N 个调用方里，说明它正在发挥巨大的深模块价值。
3. **Interface is the test surface（接口即测试表面）**：
   业务调用方和测试必须穿过同一个 seam。如果你发现必须侵入接口去测试内部私有细节，说明该模块的抽象形状设计错了。
4. **One adapter = hypothetical seam; Two adapters = real seam**：
   除非明确存在至少两个 adapters（通常是生产真实实现 + 测试内存替身），否则不要凭空引入 seam。单 adapter 的 seam 往往只是无意义的过早抽象。

---

## 被否决的传统构陷（Rejected Framings）

- ❌ **把 Depth 理解为“代码行数多”**（Ousterhout 原始论文陷阱）：这会反向鼓励把代码写得冗长臃肿。这里严格奉行 **Depth-as-leverage（以小接口撬动大行为）**。
- ❌ **把 Interface 狭义理解为语言的 `interface` 关键字**：接口包括调用方为了不踩坑必须知道的所有不变量、顺序与错误模式。
- ❌ **泛滥的通用浅包装层（Pass-through & Middle Man）**：没有任何业务逻辑、只是把入参转给下一层调用的空壳包装器。

---

## 扩展指引

- **深化依赖集群**：见 [DEEPENING.md](DEEPENING.md)（依赖分类、接缝纪律与测试替换战略）；
- **方案二次设计**：见 [DESIGN-IT-TWICE.md](DESIGN-IT-TWICE.md)（并行子 Agent 探索截然不同的接口方案）。
