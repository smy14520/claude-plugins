---
name: grilling
description: "Interview the user relentlessly about a plan, decision, or spec using a design tree. Use when stress-testing ideas, refining scope, resolving technical branches, or when mentioning 'grill', 'interview', 'clarify requirements'."
---

# Grilling — 决策树与前沿推进访谈

访谈的目标是建立严谨的决策树模型，逐轮遍历决策前沿（Frontier），直到消除一切隐藏假设，达成坚实的工程共识。

## 决策树与轮次（Design Tree & Frontier）

1. **设计树模型**：
   - 每个决策都会分叉出依赖于它的下级子决策；
   - **Frontier（前沿）**：所有前置依赖已经解决、当前可以诚实提问的决策集合。
2. **轮次推进规则（Rounds）**：
   - 每一轮只提问当前 Frontier 上的问题；
   - 每一个问题必须编号，并**附带推荐选项与推荐理由**（人类只需确认或纠偏，无需从零打字）；
   - 前置决策未定时，其下级子决策严禁提前抛出；
   - **Completion criterion per round**：收到人类本轮回答后，重新计算 Frontier，再推进下一轮。

## 事实与决策分工（Facts vs. Decisions）

- **查事实是 Agent 的绝对职责**：
  - 严禁向用户询问“某个文件叫什么”、“当前某个函数怎么实现的”、“数据库用的什么版本”；
  - 遇到事实空白，派发 Subagent 检索代码库或通过 WebSearch 查阅官方文档。
- **做选择是人类的特权**：
  - 只有在面临真正的业务、架构或成本取舍时，才将选项呈递给人类。

## 隐性假设显影（Common Ground）

在提出推荐选项或敲定核心深接缝（Seams）前，模型必须主动向人类**显式坦白暗中做出的技术与业务假设**（杜绝因 AI 脑补导致的认知鸿沟）：
- **主动交代**：“*为了推进这个设计，我暗中假设了以下事实（如数据规模、存储位置、幂等性要求、错误容忍度），若有不符请纠偏*”；
- 经过人类确认或纠偏后的关键技术假设，落盘至 `spec.md` 的 `## Latent Assumptions Exposed`。

## 遇阻外援通道（Detours）

- **经验性分叉（跑起来才知道）**：
  - 遇到关于 UI 视觉、交互手感、复杂并发状态模型的争议，**立即发起 `prototype` 技能**；
  - 在 `.forge/prototypes/<slug>/` 生成单文件探针，人类体验获取实证结论（Verdict）后折回主线。
- **术语模糊与概念多义**：
  - 调用 `domain-modeling` 技能，与人类统一名词，并沉淀入 `.forge/wiki/` 或 `.claude/rules/`。

## 最终退出准则（Final Completion Criterion）

- Frontier 为空：整棵设计树的分支已全部到达叶子节点，无沉默假设；
- **隐性假设已澄清**：`## Latent Assumptions Exposed` 经过人类确认；
- **锁定成果呈现**：在屏幕上显式呈现提炼出的 2~3 个核心 **Agreed Seams（深接缝）** 与 **Out of Scope** 清单；
- 人类确认达成共识后，将契约落盘至 `spec.md`。

## 反模式（Anti-Patterns）

- **Fact-Interrogation**：把用户当数据库，盘问可以通过阅读代码获知的客观事实。
- **Out-of-Order Questioning**：前置技术路线还没定，就开始问底层的参数细节。
- **Unrecommended Blank Questions**：只扔出抽象大问题而不给推荐选项与取舍依据。
- **Accepting Ambiguity**：对“大概”、“尽量”等模糊修饰语含糊带过，未追问明确边界。
