---
name: wayfinder
description: "把单个 agent 会话装不下的超大、模糊工作规划为共享决策地图（Decision Map），并逐一攻克决策票，直到通往目标的路线完全清晰。适用于全新大项目或大规模架构重构。"
disable-model-invocation: true
---

# Wayfinder — 迷雾工程决策探路

一个松散的想法出现了：它太大，单个 Agent 会话装不下，而且被重重迷雾（Fog）包围；从这里到**目的地（Destination）**的路线还看不见。

Wayfinder 的目标是**找到这条清晰的路，而不是朝目的地盲目猛冲**。这个技能把复杂的路径绘制在项目本地工作区 `.forge/maps/<slug>/` 中，形成一张**共享地图（Shared Map）**，然后通过逐个攻克**决策票（Decision Tickets）**——它们承载需要拍定决策才能推进的未知，而不是机械执行的业务切片——直到整个工程路线完全明朗。

不同工程的 Destination 不同，而**为 Destination 命名是制图的第一个动作**；它直接塑造后续的每一张票。它可以是一份待移交并迭代的完整架构 Spec、一个在正式规划前必须锁定的核心决策、或一次原地完成的数据结构大迁移。

---

## 规划先行，坚决不越界编码（Plan, don't do）

Wayfinder 默认且强制用于 **规划（Planning）**：
- 每张票解决一个关键决策；当团队动手前已经没有任何事情需要纠结、路径 100% 清晰时，地图才算完成；
- 想顺手写业务代码的冲动通常表明你已经到达了地图边缘，该移交了；
- **核心铁律：本技能只产出 Decisions（拍定的决策），绝不产出 Deliverables（业务交付代码）。**

---

## 始终用全名称呼（Refer by name）

每张地图和每张票都是有身份的实体，拥有一个**清晰的名字（Title）**。在所有给人看的叙述、以及地图的 Decisions-so-far 中，**必须使用全名引用它，严禁只写裸 ID（如 `#42` 或 `T-001`）**。纯数字难以辨认，名字一眼就能看懂。

---

## 纯 Markdown 地图规范（The Map in `.forge/maps/<slug>/`）

地图落盘在 `.forge/maps/<slug>/map.md`，是唯一的规范档案（Canonical Artifact）。它的具体决策票存放于同级目录的 `tickets/`。

地图是**索引（Index）**，不是原始数据仓库。它列出已经做出的决策，并链接指向保存讨论细节的 tickets。**一个决策只存在于一个地方，也就是它的票里**。

### 地图正文结构模板（`map.md`）

```markdown
# 迷雾决策地图: {Map Title}

## Destination (目的地)

<!-- 简述达到本工程终点时的具体形态：是一份落盘的 Spec、一个拍定的核心架构决策、还是系统大迁移方案？1~2 句话锚定全部 Scope -->

## Notes (工程备忘与偏好)

<!-- 业务领域、每个会话必须参考的规范文档、本工程长期不变的架构偏好 -->

## Decisions so far (已拍定的决策索引)

<!-- 索引清单：每张 Closed 决策票占一行，附带单行结论摘要与票链接。后续会话一眼看懂走过的路线 -->
- [T-001-xxxx](tickets/T-001-xxxx.md) — 单行结论摘要

## Not yet specified (Fog of war 模糊区)

<!-- 参见“Fog of war”节：在 Scope 范围内但当前还说不清楚、无法立票的朦胧区域；随着前沿推进逐步升级为票 -->
- 迷雾区域描述 1

## Out of scope (明确排除边界)

<!-- 参见“排除边界”节：明确裁定在目的地之外的工作；一经关闭，永不升级为票 -->
- [T-003-xxxx](tickets/T-003-xxxx.md) — 排除的原因摘要
```

---

## 决策票规范（Tickets in `tickets/T-NNN-<slug>.md`）

每张票的大小必须严格控制在**单个会话能够彻底攻克**的粒度内：

```markdown
# T-001: {清晰的决策议题标题}

**类型 (Type):** `grilling` | `prototype` | `research` | `task`
**执行模式 (Mode):** `HITL` (需人类在线裁决) | `AFK` (Agent 可独立完成)
**依赖阻塞 (Blocked by):** `none` 或其他前置票名 (如 `T-000-destination`)

## Question (核心待决议题)

详细阐述本张票必须解决的单个核心决策或调查目标。
```

### 票的四种类型学（Ticket Types）

每张票必须标明是 **HITL**（Human in the loop，必须与能代表业务发言的人类一起处理）还是 **AFK**（Agent 可独立运行）：
- **Research（AFK）**：查阅外部官方文档、第三方 API 或既有知识库，找出决策正在等待的事实。派发子 Agent 异步解决。
- **Prototype（HITL）**：通过粗糙、自包含的 Spike 原型提高讨论置信度（调用 `prototype` 技能在 `.forge/prototypes/` 探索），核心问题是“跑起来手感如何”或“外观长什么样”时使用。
- **Grilling（HITL）**：决策树深度访谈。**默认类型**。调用 `grilling` 与 `domain-modeling` 技能，通过前沿推进把方案彻底聊透。
- **Task（HITL 或 AFK）**：做出决策前必须完成的手工准备工作（如：申请外部沙盒账号、准备脱敏测试数据集）。**这是唯一会动手的类型，但它凭借“解锁后续决策”而存在，绝不是为了交付业务代码**。

---

## 迷雾探索法则（Fog of War）

地图是**有意不完整**的：不要描绘你还看不见的东西。Tickets 之外是 Fog of war：那些你能隐约感觉到以后会来的决策，但它们悬在尚未解决的前置问题之上，暂时还无法钉住。

**Fog or Ticket？（是 Fog 还是立票？）判据绝对分明**：
- **可以立票（Ticket）**：如果你**现在就能把问题精确表述清楚**（哪怕它被前置票 Blocked 暂时不能做），立刻建票！
- **留在迷雾（Not yet specified）**：如果你现在还说不清楚，坚决不要把 Fog 预先切成小票！Fog of war 比票粗大得多，当工期推移到该区域时，一片 Fog 可能分化出 3 张票，也可能一张都没有。

---

## 明确排除边界（Out of Scope）

迷雾只会聚集在通往 Destination 的路线上。超出 Destination 的工作是 **Out of scope**，不是迷雾。
- 如果某张票在讨论中被发现超出了目的地范围，立即将该票 **Close**，并在地图的 `## Out of scope` 节记录一行原因和该票的链接；
- **Out of scope 永远不会升级**，它直接代表了本工程坚决不做的边界。

---

## 执行操典（Invocation）

### 模式 1：制图探路（Chart the map — 首个会话）
1. **命名 Destination**：调用 `grilling` 确定地图要找到的终点形态；
2. **绘制前沿 Frontier**：进行广度优先的快速扫视，浮现当前能看清的决策。**如果没有迷雾，说明路线极短，根本不需要建地图，直接停机去干活**；
3. **初始化地图**：在 `.forge/maps/<slug>/map.md` 写入结构，把看不清的列入 `Not yet specified`；
4. **创建第一批票**：创建当前能说清的 tickets，并标明 `Blocked by` 依赖关系；
5. **停止会话**：制图本身就是一个完整会话，首个会话坚决不手动画票执行。

### 模式 2：攻克决策票（Work through the map — 后续会话）
1. 读取 `map.md`，加载全局低分辨率视图；
2. 挑选一张当前 **未被阻塞（Unblocked）的前沿票**；
3. **单会话单票纪律：每个会话绝不解决超过 1 张决策票（Research 调研除外）**；
4. 攻克完成后，在该票中记录拍定的答案与依据，将票关闭，并在 `map.md` 的 `## Decisions so far` 追加一行结论索引；
5. 将迷雾区中已经能够说清的问题，晋升（Graduate）为新的 tickets。
6. **迷雾散尽即交棒**：当地图所有前沿票均已关闭，迷雾清空时，正式移交至 `/develop` 开启业务施工。
