---
name: to-spec
description: "把当前对话转成 spec 并落盘到本地 .forge/<slug>/spec.md——不做访谈，只综合已经讨论的内容。在对齐后的需求要跨多个会话实现、需要先沉淀成 spec 时使用。"
---

这个 skill 使用当前 conversation context 和 codebase understanding 产出 spec。**不要**访谈用户，只综合你已经知道的内容。

## Process

1. 如果还没有探索 repo，先探索它以理解 codebase 当前状态。在 spec 中始终使用项目 domain glossary vocabulary，并遵守相关 ADRs。

2. 草拟你准备在哪些 seams 上测试这个 feature。优先使用现有 seams，而不是新增 seams。使用尽可能高层的 seam。如果确实需要新增 seams，尽可能在最高层提出。

Seams 越少越好，理想数量是一个。与用户确认这些 seams 是否符合预期。

3. 使用下面模板写 spec，并保存到本地 `.forge/<slug>/spec.md`。

<spec-template>

## Problem Statement

用户正在面对的问题，从用户视角描述。

## Solution

问题的解决方案，从用户视角描述。

## Requirements

详尽的编号列表，从用户视角覆盖 feature 的全部可感知功能与交互行为（可按主题小标题分组，全文保持连续编号以便引用与对账）：

1. <用户场景或触发动作>：<用户可感知的外部行为与结果>

<requirement-example>
1. 按快捷键（默认 `⌥+S`）或点击扩展图标一键静默剪藏当前页，不弹出任何表单；保存成功后图标切换为「已收藏」态并提供直达链接
2. 同一页面多次划词摘录时，自动聚合追加到同一条剪藏条目中，不产生碎片条目
</requirement-example>

这里只写用户可感知的功能行为（涉及多角色时显式标明角色）；意图自明的直接写行为，仅在取舍非显而易见时用括号简短注一句原因。底层协议、重试策略、存储结构、安全校验等技术决策统一放进下面的 `Implementation Decisions`，上下半场不重复。

## Implementation Decisions

已作出的技术与架构决策列表（每项决策只在此处单点记录，不与 `Requirements` 重复，也不另起冗余章节）。可以包括：

- 将 build/modify 的 modules
- 将 modify 的 module interfaces
- 来自 developer 的技术澄清与工程硬约束
- Architectural decisions
- Schema changes
- API contracts、协议边界与可靠性机制（如幂等、退避重试、安全校验）
- Specific interactions

不要包含具体 file paths 或 code snippets。它们可能很快过时。

例外：如果 prototype 产出的 snippet 比 prose 更精确地编码了某个决策（state machine、reducer、schema、type shape），可以内联到相关 decision 中，并简短说明它来自 prototype。只保留决策密集部分，不要放完整 working demo。

## Testing Decisions

已作出的 testing decisions 列表。包括：

- 什么是好测试的描述（只测试 external behavior，不测试 implementation details）
- 哪些 modules 会被测试
- 测试的 prior art（即 codebase 中类似类型的 tests）

## Out of Scope

本 spec 范围外事项的描述。

## Further Notes

关于 feature 的其他 notes。

</spec-template>
