# Design It Twice

当用户想为某个 deepening candidate 探索替代 interfaces 时，使用这个并行 sub-agent 模式。它源自 John Ousterhout 的 "Design It Twice" 理念：你的第一个想法往往不是最好的。

全程严格使用 [SKILL.md](SKILL.md) 中的词汇：**module**、**interface**、**seam**、**adapter**、**leverage**。

## 流程（Process）

### 1. 定义问题空间（Frame the problem space）
在启动 sub-agents 前，先写一段面向用户的问题空间说明：
- 新 interface 需要满足的硬性 constraints；
- 它所依赖的 dependencies 属于哪一类（参见 [DEEPENING.md](DEEPENING.md)）；
- 一个粗略的示意代码草稿（illustrative code sketch），只用来让约束具象化。

### 2. 派发并行子 Agent（Spawn sub-agents）
并行派生 3 个以上的独立 sub-agents。每个 agent 必须为 deepened module 产出一套**截然不同（Radically Different）**的 interface 设计方案。

给每个 agent 不同的设计约束方向：
- **Agent 1（极简杠杆）**: "Minimize the interface - aim for 1-3 entry points max. Maximise leverage per entry point."
- **Agent 2（高扩展性）**: "Maximise flexibility - support many use cases and extension."
- **Agent 3（主流优先）**: "Optimise for the most common caller - make the default case trivial."
- **Agent 4（跨接缝）**: "Design around ports & adapters for cross-seam dependencies."

每个 sub-agent 必须输出：
1. **Interface 契约**（方法名、入参出参、不变量 invariants、顺序约束、错误模式）；
2. **Caller 使用范例**；
3. **Seam 内部隐藏的具体实现细节**；
4. **依赖策略与 Adapters**（参见 [DEEPENING.md](DEEPENING.md)）；
5. **Trade-offs 权衡**：leverage 哪里厚、哪里薄。

### 3. 汇总呈现与对比（Present and compare）
向用户并排对比各方案的优劣，等待用户拍板决定最终走向。
